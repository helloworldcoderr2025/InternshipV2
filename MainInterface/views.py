from django.shortcuts import render,redirect
from collections import defaultdict, deque
from django.contrib import messages
from django.contrib.auth.models import User,auth
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
import pandas as pd
import re
import json
from .models import Student,Registrations,Company,AuthUser,Documents,UserType,Announcements,CompanyJobprofiles,CompanyInvitations
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import AnonymousUser
from django.core.mail import send_mail
from django.conf import settings
from .models import Mails
import csv
import io
import openpyxl
from django.utils.crypto import get_random_string
from supabase import create_client
import urllib.parse
import random
def extract_relative_path(full_url):
    parsed = urllib.parse.urlparse(full_url)
    # Assuming bucket is 'profile-pics', path after '/profile-pics/' is what we want
    path_parts = parsed.path.split('/storage/v1/object/public/profile-pics/')
    if len(path_parts) == 2:
        return path_parts[1]
    return None

# Homepage view
def home_page_view(request):
    return render(request, 'Home_page.html')

# Uploadpage view
def upload_page_view(request):
    # Checking the uploaded file and reading the data from it
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        try:
            # Read the file based on its extension (CSV or Excel)
            if uploaded_file.name.endswith('.csv'):
                fp = pd.read_csv(uploaded_file)  # fp - file pointer for CSV
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                fp = pd.read_excel(uploaded_file)  # fp - file pointer for Excel
            else:
                messages.error(request, "Unsupported file type. Please upload a CSV or Excel file.")
                return render(request, 'Upload_page.html')

            # Preview data for displaying the first 10 rows
            preview_data = fp.head(10).to_html(classes="table", index=False)

        except Exception as e:
            messages.error(request, f"Error reading file: {str(e)}")
            return render(request, 'Upload_page.html')

        # Handling the dynamic table creation
        table_name = re.sub(r'\W+', '_', uploaded_file.name.split('.')[0].lower())  # Table name based on file name
        columns = [re.sub(r'\W+', '_', col.strip().lower()) for col in fp.columns]  # Columns from the file
        column_datatype = ', '.join([f'"{col}" TEXT' for col in columns])  # Setting column datatype as TEXT

        try:
            # Creating the table if it doesn't exist
            with connection.cursor() as cur:
                cur.execute(f'CREATE TABLE "{table_name}" ({column_datatype});')
                messages.success(request, "Table created successfully!")
        except Exception as e:
            messages.error(request, "Table already exists! Use the edit option to modify it.")
            return redirect('upload_page')  # Redirect to edit the table if it already exists

        # Inserting data from the uploaded file into the database table
        try:
            with connection.cursor() as cur:
                for _, row in fp.iterrows():
                    values = [str(v) if pd.notna(v) else None for v in row]  # Convert NaN values to None
                    placeholders = ', '.join(['%s'] * len(values))  # Placeholders for SQL
                    column_names = ', '.join([f'"{col}"' for col in columns])  # Column names for SQL query

                    cur.execute(
                        f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})',
                        values
                    )
                messages.success(request, "Data inserted successfully!")
        except Exception as e:
            messages.error(request, "Table already exists, For modification use the edit")
            return render(request, 'Upload_page.html',{'preview': preview_data})

        # Rendering the upload page with a preview of the data
        return render(request, 'Upload_page.html', {'preview': preview_data})

    return render(request, 'Upload_page.html')


# View Selected table view
def view_selected_table_view(request):
    table_name = request.GET.get('table_name')
    if not table_name:
        messages.error(request,"No table is selected")
        return redirect('edit_page')
    try:
        with connection.cursor() as cur:
            cur.execute(f'SELECT * FROM "{table_name}" LIMIT 10')
            columns = [ col[0] for col in cur.description ]
            rows = cur.fetchall()

        fp = pd.DataFrame(rows,columns=columns)
        return HttpResponse(fp.to_html(classes="table", index=False))
    except Exception as e:
        messages.error(request,"Error reading the table from the database")
        return redirect('edit_page')

# Editpage view
def edit_page_view(request):
    with connection.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' and tablename NOT LIKE 'django%' and tablename NOT LIKE 'auth%'; ")
        list_of_tables = [table[0] for table in cur.fetchall()]

    if request.method == 'POST':
        selected_table = request.POST.get('table_name')
        mode = request.POST.get('mode')
        uploaded_file = request.FILES.get('file')

        if not selected_table or not mode or not uploaded_file :
            messages.error(request,"Some fields are missing please check and try again")
            return render(request,'Edit_page.html',{'list_of_tables':list_of_tables})
        
        try:
            if uploaded_file.name.endswith('.csv'):
                fp = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls','.xlsx')):
                fp = pd.read_excel(uploaded_file)
            else:
                messages.error(request,"Unsupported File")
                return render(request,'Edit_page.html',{'list_of_tables':list_of_tables})

        except Exception as e:
            messages.error(request,"Failed to read the file")
            return render(request,'Edit_page.html',{'list_of_tables':list_of_tables})
        
        # Extracting the column info from new file
        columns = [re.sub(r'\W+', '_', col.strip().lower()) for col in fp.columns] #New file columns
        column_and_datatypes = ', '.join([f'"{col}" TEXT' for col in columns])

        try:
            with connection.cursor() as cur:

                if mode == 'recreate': # mode-1
                    cur.execute(f'DROP TABLE IF EXISTS "{selected_table}"') #Drop the table

                    #Creating the new table
                    cur.execute(f' CREATE TABLE IF NOT EXISTS "{selected_table}" ({column_and_datatypes})')

                    #Inserting the data into the table
                    for _,row in fp.iterrows():
                        values = [ str(row[col]) for col in fp.columns ]
                        placeholders = ','.join(['%s']*len(values))
                        column_names = ','.join(f'"{col}"' for col in columns)
                        cur.execute(f' INSERT INTO {selected_table} ({column_names}) VALUES ({placeholders})',values)
                    
                    messages.success(request,"Table is recreated successfully!!")

                elif mode == 'add_columns':  # mode-2
                    # Mapping original column names to cleaned DB column names
                    colmap = {
                        col: re.sub(r'\W+', '_', col.strip().lower())
                        for col in fp.columns
                    }
                    columns = list(colmap.values())  # cleaned column names

                    # Fetch existing columns from the DB
                    cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = 'public';""", [selected_table])
                    existing_columns_raw = {str(col[0]) for col in cur.fetchall()}
                    existing_columns = {re.sub(r'\W+', '_', col.strip().lower()) for col in existing_columns_raw}

                    # Identify new columns
                    new_columns = [colmap[col] for col in fp.columns if colmap[col] not in existing_columns]
                    if not new_columns:
                        messages.info(request, "No new columns found to add.")
                        return render(request, 'Edit_page.html', {'list_of_tables': list_of_tables})

                    # Add new columns to DB
                    try:
                        for original_col, cleaned_col in colmap.items():
                            if cleaned_col in new_columns:
                                cur.execute(f'ALTER TABLE "{selected_table}" ADD COLUMN "{cleaned_col}" TEXT')
                    except Exception as e:
                        messages.error(request, f"Error adding the column: {str(e)}")
                        return render(request, 'Edit_page.html', {'list_of_tables': list_of_tables})

                    # Optional: clear all old data before re-inserting (depends on your logic)
                    try:
                        cur.execute(f'DELETE FROM "{selected_table}"')

                        for _, row in fp.iterrows():
                            # Use original columns to get data, and cleaned columns to insert
                            values = [str(row.get(orig_col, None)) for orig_col in fp.columns]
                            placeholders = ','.join(['%s'] * len(values))
                            column_names = ','.join(f'"{colmap[orig_col]}"' for orig_col in fp.columns)
                            cur.execute(
                                f'INSERT INTO "{selected_table}" ({column_names}) VALUES ({placeholders})',
                                values
                            )
                        messages.success(request, "New columns along with their data inserted successfully")
                    except Exception as e:
                        messages.error(request, f"Columns added but error in data insertion: {str(e)}")
                        return render(request, 'Edit_page.html', {'list_of_tables': list_of_tables})

                elif mode == 'del_columns': # mode-3
                    # Fetch existing columns from the DB
                    cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = 'public';""", [selected_table])
                    existing_columns_raw = [row[0] for row in cur.fetchall()]
                    existing_columns = [re.sub(r'\W+', '_', col.strip().lower()) for col in existing_columns_raw]

                    columns_to_be_removed = [ col for col in existing_columns if col not in columns ]

                    try:
                        for col in columns_to_be_removed:
                            cur.execute(f'ALTER TABLE "{selected_table}" DROP COLUMN "{col}"')
                        messages.success(request,"Non-existing columns are removed successfully")
                    except Exception as e:
                        messages.error(request,"Failed to remove the non-existing columns")
                        return render(request, 'Edit_page.html', {'list_of_tables': list_of_tables})


                elif mode == 'add_data': # mode-4
                    # Checking for anyother changes which can violate this mode of operation
                    cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s;""",[selected_table])
                    existing_columns = [row[0] for row in cur.fetchall()]

                    for col in columns:
                        if col not in existing_columns or len(columns)!=len(existing_columns):
                            messages.error("Table Structure is different check it properly")
                            return render(request,'Edit_page.html', {'list_of_tables': list_of_tables})
                    
                    # Appending the new data into the database before that checking it data is existing or not
                    try:
                        for _,row in fp.iterrows():
                            values = [str(row.get(col,None)) for col in existing_columns]
                            placeholders = ','.join(['%s']*len(values))
                            column_names = ','.join(f'"{col}"' for col in existing_columns)
                            where_condition = ' AND '.join(f'"{col}" = %s' for col in existing_columns)
                            cur.execute(f'SELECT 1 FROM "{selected_table}" WHERE {where_condition} LIMIT 1',values)
                            #Row doesnt exist
                            if not cur.fetchone(): 
                                cur.execute(f'INSERT INTO "{selected_table}" ({column_names}) VALUES ({placeholders})', values)
                        messages.success(request,"New Data is appended to the existing data successfully")   
                    except Exception as e:
                        messages.error(request,"Error appending the data try again")
                        return render(request,'Edit_page.html',{'list_of_tables':list_of_tables})
                        
                elif mode == 'overwrite': # mode-5
                    cur.execute(f'DELETE FROM "{selected_table}"') #Removing all the existing data
                    try:
                        for _, row in fp.iterrows():
                            db_columns = [ col.strip() for col in fp.columns ]
                            values = [row[col] for col in db_columns]
                            placeholders = ','.join(['%s'] * len(values))
                            column_names = ','.join(f'"{col}"' for col in columns)
                            cur.execute(f'INSERT INTO "{selected_table}" ({column_names}) VALUES ({placeholders})', values)
                        messages.success(request,"Table overwritten successfully")
                    except Exception as e:
                            messages.error(request,"Error overwriting use a suitable mode")

                else: 
                    messages.error(request,"Invalid mode got selected")
                
        except Exception as e:
            messages.error(request, f"Database error: {str(e)}")
        return render(request,'Edit_page.html',{'list_of_tables':list_of_tables})

    return render(request,'Edit_page.html',{'list_of_tables':list_of_tables})


# Homepage dyamic content loading logic
def get_columns_view(request):
    table_name = request.GET.get('table_name')
    if not table_name:
        return JsonResponse({'error':'Table name not provided'},status=400)
    try:
        with connection.cursor() as cur:
            cur.execute(""" SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = 'public';""", [table_name])
            columns = [row[0] for row in cur.fetchall()]
        return JsonResponse({'columns':columns})
    except Exception as e:
        return JsonResponse({'error':str(e)},status=500)
    
def get_columns_view(request):
    table_name = request.GET.get('table_name')
    if not table_name :
        return JsonResponse({'error':'Table name not provided'},status=400)
    try:
        with connection.cursor() as cur:
            cur.execute(""" SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = 'public';""", [table_name])
            columns = [row[0] for row in cur.fetchall()]
        return JsonResponse({'columns':columns})
    except Exception as e:
        return JsonResponse({'error': str(e)},status=500)
    
def get_distinct_column_values_view(request):
    table = request.GET.get('table')
    column = request.GET.get('column')

    if not table or not column:
        return JsonResponse({'error':'Missing table_name or column parameter '})
    try:
        with connection.cursor() as cur:
            cur.execute( f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL LIMIT 100')
            values = [ str(row[0]) for row in cur.fetchall() ]
        return JsonResponse({'values':values})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_all_tables_view(request):
    # For PostgreSQL:
    with connection.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' and tablename NOT LIKE 'django%' and tablename NOT LIKE 'auth%'; ")
        tables = [row[0] for row in cur.fetchall()]
    return JsonResponse({'tables': tables})



def restore_type_and_cast(val):
    """Restore Python type and provide corresponding SQL CAST type."""
    if val is None:
        return None, None
    try:
        int_val = int(val)
        return int_val, 'INTEGER'
    except (ValueError, TypeError):
        pass
    try:
        float_val = float(val)
        return float_val, 'REAL'
    except (ValueError, TypeError):
        pass
    if isinstance(val, str) and val.lower() in ['true', 'false']:
        return val.lower() == 'true', 'BOOLEAN'
    return val, None  # Treat as TEXT

@csrf_exempt
def submit_query_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        tables = data.get('tables', [])
        output_columns = data.get('outputColumns', {})
        conditions = data.get('conditions', [])
        joins = data.get('joins', [])

        if not tables:
            return JsonResponse({'error': 'No tables selected'}, status=400)

        base_table = tables[0]

        # SELECT clause
        select_cols = []
        for table in tables:
            for col in output_columns.get(table, []):
                select_cols.append(f"{table}.{col}")
        select_cols_str = ', '.join(select_cols) if select_cols else '*'

        # JOIN graph construction
        join_graph = defaultdict(list)
        join_map = {}
        for join in joins:
            t1, t2 = join['table1'], join['table2']
            join_graph[t1].append((t2, join))
            join_graph[t2].append((t1, join))
            join_map[(t1, t2)] = join
            join_map[(t2, t1)] = join  # Bi-directional

        # BFS to determine join order
        visited = set()
        queue = deque([base_table])
        visited.add(base_table)
        join_clauses = []

        while queue:
            current = queue.popleft()
            for neighbor, join in join_graph[current]:
                if neighbor in visited:
                    continue

                jtype = join.get('joinType', 'INNER').upper()
                if jtype not in ('INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'):
                    jtype = 'INNER'

                t1, c1 = join['table1'], join['column1']
                t2, c2 = join['table2'], join['column2']

                # Direction matters: make sure the base is already visited
                if current == t1:
                    clause = f"{jtype} JOIN {t2} ON {t1}.{c1} = {t2}.{c2}"
                else:
                    clause = f"{jtype} JOIN {t1} ON {t2}.{c2} = {t1}.{c1}"

                join_clauses.append(clause)
                queue.append(neighbor)
                visited.add(neighbor)

        # Construct final query
        query = f"SELECT {select_cols_str} FROM {base_table} " + " ".join(join_clauses)

        # WHERE clause
        where_clauses = []
        query_params = []

        for cond in conditions:
            col = cond.get('column')
            op = cond.get('operator', '=').strip()
            val = cond.get('value')
            table_for_col = cond.get('table') or base_table

            if val in (None, 'null', 'None'):
                if op == '=':
                    where_clauses.append(f"{table_for_col}.{col} IS NULL")
                elif op in ('!=', '<>'):
                    where_clauses.append(f"{table_for_col}.{col} IS NOT NULL")
                continue

            restored_val, cast_type = restore_type_and_cast(val)
            col_expr = f"CAST({table_for_col}.{col} AS {cast_type})" if cast_type else f"{table_for_col}.{col}"

            if op not in ('=', '!=', '<>', '>', '<', '>=', '<='):
                op = '='

            where_clauses.append(f"{col_expr} {op} %s")
            query_params.append(restored_val)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        print("Final SQL Query:", query)
        print("With Params:", query_params)

        with connection.cursor() as cursor:
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        if not rows:
            return JsonResponse({'columns': [], 'rows': [], 'message': 'No results to display'})

        return JsonResponse({'columns': columns, 'rows': rows})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)







# Contains all table related operation such as insert update delete
def table_operations_view(request):
    # Get list of tables
    with connection.cursor() as cur:
        cur.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
              AND tablename NOT LIKE 'django%' 
              AND tablename NOT LIKE 'auth%';
        """)
        list_of_tables = [table[0] for table in cur.fetchall()]

    if request.method == 'GET':
        if 'search_results' in request.session:
            context = {
                'list_of_tables': list_of_tables,
                'search_results': request.session.pop('search_results'),
                'columns': request.session.pop('search_columns'),
                'selected_table': request.session.pop('selected_table')
            }
            return render(request, 'table_operations.html', context)
        return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})

    # POST handling
    table_name = request.POST.get('table_name')
    operation = request.POST.get('operation')

    if not table_name or not operation:
        messages.error(request, "Please select both a table and an operation")
        return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})

    try:
        if operation == 'search_records':
            # Get search criteria from user 
            search_criteria = {}
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public';
                """, [table_name])
                columns = [row[0] for row in cur.fetchall()]

                for col in columns:
                    val = request.POST.get(col)
                    if val:
                        search_criteria[col] = val

                if not search_criteria:
                    messages.error(request, "Please enter at least one search criteria")
                    return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})

                where_clause = " AND ".join([f'"{k}" = %s' for k in search_criteria.keys()])
                query = f'SELECT * FROM "{table_name}" WHERE {where_clause} LIMIT 20'
                cur.execute(query, list(search_criteria.values()))
                search_results = cur.fetchall()

                if not search_results:
                    messages.info(request, "No records found matching your criteria")
                    return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})

                # Store for GET rendering
                request.session['search_results'] = search_results
                request.session['search_columns'] = columns
                request.session['selected_table'] = table_name
                request.session['operation'] = 'update_record'

                return redirect('table_operations')

        elif operation == 'update_record':
            record_id = request.POST.get('record_id')
            if not record_id:
                messages.error(request, "No record selected for update")
                return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})

            with connection.cursor() as cur:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public';
                """, [table_name])
                columns = [row[0] for row in cur.fetchall()]

                update_data = {}
                for col in columns:
                    val = request.POST.get(f'update_{col}')
                    if val is not None and val != '':
                        update_data[col] = val

                if not update_data:
                    messages.error(request, "No fields provided for update")
                    return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})

                set_clause = ", ".join([f'"{k}" = %s' for k in update_data.keys()])
                query = f'UPDATE "{table_name}" SET {set_clause} WHERE id = %s'
                cur.execute(query, list(update_data.values()) + [record_id])

                messages.success(request, f"Record {record_id} updated successfully")
                return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})

        elif operation == 'delete_column':
            column_name = request.POST.get('column_name')
            with connection.cursor() as cur:
                cur.execute(f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"')
            messages.success(request, f"Column '{column_name}' deleted successfully from '{table_name}'")

        elif operation == 'delete_row':
            row_id = request.POST.get('row_id')
            pk_column = request.POST.get('pk_column')  # Get the primary key column name
    
            if not row_id or not pk_column:
                messages.error(request, "Missing row ID or primary key column")
                return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})
    
            try:
                with connection.cursor() as cur:
                    cur.execute(f'DELETE FROM "{table_name}" WHERE "{pk_column}" = %s', [row_id])
                messages.success(request, f"Row deleted successfully")
            except Exception as e:
                messages.error(request, f"Error deleting row: {str(e)}")

        elif operation == 'add_column':
            column_name = request.POST.get('column_name')
            data_type = request.POST.get('data_type')
            with connection.cursor() as cur:
                cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {data_type}')
            messages.success(request, f"Column '{column_name}' of type '{data_type}' added successfully to '{table_name}'")

        elif operation == 'add_row':
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public';
                """, [table_name])
                columns = [row[0] for row in cur.fetchall()]

            values = []
            for col in columns:
                value = request.POST.get(col)
                values.append(value if value != '' else None)

            placeholders = ', '.join(['%s'] * len(values))
            column_names = ', '.join([f'"{col}"' for col in columns])
            with connection.cursor() as cur:
                cur.execute(f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})', values)

            messages.success(request, f"New row added successfully to '{table_name}'")

        else:
            messages.error(request, "Invalid operation selected")

    except Exception as e:
        messages.error(request, f"Database error: {str(e)}")

    return render(request, 'table_operations.html', {'list_of_tables': list_of_tables})


# AJAX endpoint to get columns for a table
def get_table_columns_view(request):
    table_name = request.GET.get('table_name')
    if not table_name:
        return JsonResponse({'error': 'Table name not provided'}, status=400)
    
    try:
        with connection.cursor() as cur:
            cur.execute("""SELECT column_name FROM information_schema.columns 
                          WHERE table_name = %s AND table_schema = 'public';""", [table_name])
            columns = [row[0] for row in cur.fetchall()]
        return JsonResponse({'columns': columns})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    



def get_row_ids_view(request):
    table_name = request.GET.get('table_name')
    if not table_name:
        return JsonResponse({'error': 'Table name not provided'}, status=400)
    
    try:
        with connection.cursor() as cur:
            # First try to get the primary key column(assuming  that primary key is  the first row)
            cur.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
            """, [table_name])
            pk_column = cur.fetchone()
            
            if not pk_column:
                # If no primary key, use the first column
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    LIMIT 1
                """, [table_name])
                pk_column = cur.fetchone()
            
            if not pk_column:
                return JsonResponse({'error': 'No columns found in table'}, status=400)
            
            pk_column = pk_column[0]
            cur.execute(f'SELECT "{pk_column}" FROM "{table_name}" LIMIT 100')
            row_ids = [row[0] for row in cur.fetchall()]
            
            return JsonResponse({
                'row_ids': row_ids,
                'pk_column': pk_column
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_row_data_view(request):
    table_name = request.GET.get('table_name')
    row_id = request.GET.get('row_id')
    pk_column = request.GET.get('pk_column')  # Get the primary key column name
    
    if not table_name or not row_id or not pk_column:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        with connection.cursor() as cur:
            cur.execute(f'SELECT * FROM "{table_name}" WHERE "{pk_column}" = %s', [row_id])
            columns = [col[0] for col in cur.description]
            row_data = cur.fetchone()
            
            if not row_data:
                return JsonResponse({'error': 'Row not found'}, status=404)
            
            data = dict(zip(columns, row_data))
            return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# ############################################################################################################
levelId = {
    "Applied": 1,
    "CV Screening": 2,
    "Aptitude Test": 3,
    "GD": 4,
    "Coding Test": 5,
    "Technical Interview": 6,
    "Technical Round 2": 6,
    "HR Interview": 7,
    "Offer": 8
    } 

def is_tp(user):
    if user.is_authenticated:
        try:
            userType = UserType.objects.get(id=user.username)
            return userType.type == "T&P"
        except UserType.DoesNotExist:
            return False
    return False

def is_tp_or_StuCoordinator(user):
    if user.is_authenticated:
        try:
            userType = UserType.objects.get(id=user.username)
            return userType.type == "T&P" or userType.type=="StudentCoordinator"
        except UserType.DoesNotExist:
            return False
    return False

def index(request):
    studentFound=False
    registered=False
    send=[]
    if request.method=="POST":
        rollNumber=request.POST['rollNumber']
        try :
            print('hello1')
            student=Student.objects.get(roll_no=rollNumber)
            print('2')
            studentFound=True
            if student.registered=="Yes":
                registered=True
                try: 
                    print('3')
                    register=Registrations.objects.filter(rollnumber__iexact=rollNumber)
                    for reg in register:
                        print(4)
                        # print(reg.student)
                        company=Company.objects.get(id=reg.company_id)
                        level = levelId.get(reg.level, 0)
                        print("reg.level",reg.level)
                        ob={"companyName":company.name,"status":reg.status,"level":level}
                        print("ob",ob)
                        send.append(ob)
                except Exception as e:
                    print(e)

                
        except Exception as e:
            print(e)
            messages.info(request,"Student Doesn't Exist")
            student=None
            studentFound=False
        print(send)
        return render(request,'index.html',{'studentFound':studentFound,'student':student,'registered':registered,'send':send})
    else:
        announcements=list(Announcements.objects.filter())
        companies={}
        if not isinstance(request.user, AnonymousUser):
            jobs=list(CompanyJobprofiles.objects.filter().order_by("-key"))
            for job in jobs:
                companies[job.key]={"comapanyname":list(Company.objects.filter(id=job.company_id)),"job":job,}
            companies=dict(list(companies.items())[:9])
        return render(request,'index.html',{'announcements':announcements,"companies":companies})
    
def register(request):
    if request.method=="POST":
        redirect("otpverification")
        rollNum=request.POST['rollNum']
        branches={1:"BIO",2:"CHE",3:"CIV",4:"CSE",5:"EEE",6:"ECE",7:"MEC",8:"MME"}
        name=request.POST['name']
        year=request.POST['year']
        email=request.POST['email']
        passwd1=request.POST['password1']
        passwd2=request.POST['password2']
        interest=request.POST['job_interest_type']
        mobile=request.POST['mobileNo']
        cgpa=request.POST['cgpa']
        gate=request.GET.get('gate','NIL')
        backlogs=request.POST['backlogs']
        placed=request.POST['placed']
        linkedin=request.POST['linkedin']
        willing=request.POST['willing']
        profilepic=request.FILES.get('profilepic')
        results=request.FILES.get('results')
        scorecard=request.FILES.get('scorecard')
        print(profilepic)
        # print(name,rollNum,dept,year,email,passwd1,interest,willing,mobile,cgpa,gate,backlogs,placed,linkedin)
        if len(rollNum) != 6:
            messages.info(request, "Enter a Valid Roll Number Given by Institute")
            return render(request, "register.html", {
                'name': name,
                'rollNum': rollNum,
                'year': year,
                'email': email,
                'job_interest_type': interest,
                'mobileNo': mobile,
                'cgpa': cgpa,
                'backlogs': backlogs,
                'placed': placed,
                'linkedin': linkedin,
                'willing': willing,
                'gate':gate,
            })
        if Student.objects.filter(roll_no=rollNum).exists():
            messages.info(request,"Roll Number already Exist .. Kindly Login")
            return render(request, "register.html", {
                            'name': name,
                            'rollNum': rollNum,
                            'year': year,
                            'email': email,
                            'job_interest_type': interest,
                            'mobileNo': mobile,
                            'cgpa': cgpa,
                            'backlogs': backlogs,
                            'placed': placed,
                            'linkedin': linkedin,
                            'willing': willing,
                            'gate':gate,
            })  
        if len(mobile)!=10 or not mobile.isdigit():
            messages.info(request,"Enter a Valid Mobile Number")
            return render(request, "register.html", {
                'name': name,
                'rollNum': rollNum,
                'year': year,
                'email': email,
                'job_interest_type': interest,
                'mobileNo': mobile,
                'cgpa': cgpa,
                'backlogs': backlogs,
                'placed': placed,
                'linkedin': linkedin,
                'willing': willing,
                'gate':gate
            })
        if len(backlogs)>50 or not backlogs.isdigit():
            messages.info(request,"Enter a Valid Number of backlogs")
            return render(request, "register.html", {
                'name': name,
                'rollNum': rollNum,
                'year': year,
                'email': email,
                'job_interest_type': interest,
                'mobileNo': mobile,
                'cgpa': cgpa,
                'backlogs': backlogs,
                'placed': placed,
                'linkedin': linkedin,
                'willing': willing,
                'gate':gate
            })
        if passwd1 != passwd2:
            messages.info(request, "Passwords do not match")
            return render(request, "register.html", {
                'name': name,
                'rollNum': rollNum,
                'year': year,
                'email': email,
                'job_interest_type': interest,
                'mobileNo': mobile,
                'cgpa': cgpa,
                'backlogs': backlogs,
                'placed': placed,
                'linkedin': linkedin,
                'willing': willing,
                'gate':gate
            })
        try:
            cgpa_val = float(cgpa)
            if cgpa_val < 0 or cgpa_val > 10:
                raise ValueError
        except ValueError:
            messages.info(request, "Enter a valid CGPA (0–10)")
            return render(request, "register.html", {
                'name': name,
                'rollNum': rollNum,
                'year': year,
                'email': email,
                'job_interest_type': interest,
                'mobileNo': mobile,
                'cgpa': cgpa,
                'backlogs': backlogs,
                'placed': placed,
                'linkedin': linkedin,
                'willing': willing,
                'gate':gate
            })
        if not (profilepic ):
            print("error")
            messages.info(request,"Error in File Upload")
            return render(request, 'register.html', {
                'message': 'All three files are required.',
                'status': 'error'
            })
        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

            # Profile picture
            filename = f"profilepics/{get_random_string(10)}_{profilepic.name}"
            upload_response = supabase.storage.from_('profile-pics').upload(filename, profilepic.read())

            if hasattr(upload_response, 'error') and upload_response.error:
                raise Exception(f"Profile pic upload failed: {upload_response.error.message}")

            public_url = supabase.storage.from_('profile-pics').get_public_url(filename)
            if not public_url:
                raise Exception("Failed to retrieve profile picture URL.")

            # Scorecard (optional)
            if scorecard:
                gaterank = f"applications/gateresults/{get_random_string(10)}_{rollNum}.pdf"
                gate_response = supabase.storage.from_('profile-pics').upload(gaterank, scorecard.read())

                if hasattr(gate_response, 'error') and gate_response.error:
                    raise Exception(f"Scorecard upload failed: {gate_response.error.message}")

                gate_url = supabase.storage.from_('profile-pics').get_public_url(gaterank)
            else:
                gate_url = "null"

            # Results document 
            if results:
                resultsname = f"applications/results/{get_random_string(10)}_{rollNum}.pdf"
                results_response = supabase.storage.from_('profile-pics').upload(resultsname, results.read())

                if hasattr(results_response, 'error') and results_response.error:
                    raise Exception(f"Results upload failed: {results_response.error.message}")

                results_url = supabase.storage.from_('profile-pics').get_public_url(resultsname)
            else:
                results_url = "null"

        except Exception as e:
            print("Error here:", e)
            return render(request, 'register.html', {
                'message': f'Error: {str(e)}',
                'status': 'error'
            })


        dept=branches[int(rollNum)//100000]
        # student=Student.objects.create(name=name,roll_no=rollNum,branch=dept,registered=willing,
        #                                job_type=interest,email=email,academic_year=year,password=passwd1,
        #                                gate_rank=gate,mobile=mobile,cgpa=cgpa,placed=placed,backlogs=backlogs,linkedin=linkedin,profilepic=public_url)
        # student.save()
        # docs=Documents.objects.create(rollno=rollNum,results=results_url,scorecard=gate_url)
        # docs.save()
        # user=User.objects.create_user(password=passwd1,username=rollNum+"@student.nitandhra.ac.in",first_name=name,email=email)
        # user.save()
        request.session["reg_data"] = {
            "name": name,
            "roll_no": rollNum,
            "branch":dept,
            "registered":willing,
            "job_type":interest,
            "email":email,
            "academic_year":year,
            "password":passwd1,
            "gate_rank":gate,
            "mobile":mobile,
            "cgpa":cgpa,
            "placed":placed,"backlogs":backlogs,"linkedin":linkedin,"profilepic":public_url,"results":results_url,"scorecard":gate_url
        }
        request.session["next_url"] = "complete_registration"

        return redirect("otpverification")
    else:
        return render(request,"register.html")

def completeregistration(request):
    if request.session.get("otp_success"):
        data = request.session.get("reg_data")
        try:
            # Create Student
            student = Student.objects.create(
                name=data["name"],
                roll_no=data["roll_no"],
                branch=data["branch"],
                registered=data["registered"],
                job_type=data["job_type"],
                email=data["email"],
                academic_year=data["academic_year"],
                password=data["password"],  # optionally hash or securely handle
                gate_rank=data["gate_rank"],
                mobile=data["mobile"],
                cgpa=data["cgpa"],
                placed=data["placed"],
                backlogs=data["backlogs"],
                linkedin=data["linkedin"],
                profilepic=data["profilepic"]
            )
            student.save()

            # Create Documents
            docs = Documents.objects.create(
                rollno=data["roll_no"],
                results=data["results"],
                scorecard=data["scorecard"]
            )
            docs.save()

            # Create Django user
            user = User.objects.create_user(
                username=data["roll_no"] + "@student.nitandhra.ac.in",
                email=data["email"],
                password=data["password"],
                first_name=data["name"]
            )
            user.save()

            # Cleanup (optional)
            request.session.pop("reg_data", None)

            messages.success(request, "🎉 Registration completed successfully!")
            return redirect("login")

        except Exception as e:
            return HttpResponse(f"An error occurred during registration: {str(e)}")
    else:
        data = request.session.get("reg_data")
        print("hello")
        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

                    # Delete profilepic
            profilepic_path = data["profilepic"].split("/storage/v1/object/public/profile-pics/")[-1]
            supabase.storage.from_("profile-pics").remove([profilepic_path])

                    # Delete results (if not "null")
            if data["results"] != "null":
                results_path = data["results"].split("/storage/v1/object/public/profile-pics/")[-1]
                supabase.storage.from_("profile-pics").remove([results_path])

                    # Delete scorecard (if not "null")
            if data["scorecard"] != "null":
                scorecard_path = data["scorecard"].split("/storage/v1/object/public/profile-pics/")[-1]
                supabase.storage.from_("profile-pics").remove([scorecard_path])

                print("🧹 Files deleted from Supabase due to OTP failure.")
        except Exception as e:
            print("Error during Supabase file deletion:", e)
        return redirect("register")

def login(request):
    if request.method=="POST":
        email=request.POST['email']
        password=request.POST['password']
        user=auth.authenticate(username=email,password=password)
        print(email)
        print(password)
        if user is not None :
            auth.login(request,user)
            return redirect("index")
        else :
            messages.info(request,'Invalid Credentials !!!')
            return redirect("login")
    return render(request,"login.html")

def logout(request):
    auth.logout(request)
    return redirect("/")

def profile(request):
    send=[]
    roll=request.user.username.split("@")[0]
    student=Student.objects.get(roll_no=roll)
    if student.registered=="Yes":
                try: 
                    register=Registrations.objects.filter(rollnumber__iexact=roll)
                    for reg in register:
                        company=Company.objects.get(id=reg.company_id)
                        ob={"companyName":company.name,"level":levelId[reg.level],"status":reg.status}
                        send.append(ob)
                except Exception as e:
                    print(e)
    # docs=Documents.objects.get(rollno=roll)
    # print(docs.results)
    return render(request,"profile.html",{'student':student,'send':send})

def tplogin(request):
    if request.method=="POST":
        email=request.POST['email']
        password=request.POST['password']
        user=auth.authenticate(username=email,password=password)
        if user is not None :
            auth.login(request,user)
            return redirect("tpportal")
        else :
            messages.info(request,'Invalid Credentials !!!')
            return redirect("tplogin")
    return render(request,"tplogin.html")

def otpverification(request):
    if request.method == "POST":
        user_otp = request.POST.get("otp")
        actual_otp = request.session.get("otp")

        if user_otp == str(actual_otp):
            messages.success(request, "✅ OTP Verified Successfully.")
            request.session["otp_success"] = True
            return redirect("complete_registration")
        else:
            messages.error(request, "❌ Invalid OTP. Please try again.")
            request.session["otp_success"] = False
            return redirect("complete_registration")
    else:
        # Generate OTP and store in session
        otp = random.randint(1000, 9999)
        request.session["otp"] = otp

        # Send OTP via email
        try:
            recipient_email = "dummymailforme4321@gmail.com"  # Replace with actual student email
            subject = 'OTP for Registration'
            message = f"""
Dear Student,

Your One-Time Password (OTP) for registration to the Student Placement Portal is: {otp}

⏳ Note: This OTP is valid for 15 minutes.

Thank you.

Best Regards,  
Training and Placement Cell  
National Institute of Technology Andhra Pradesh
"""
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=False)
        except Exception as e:
            print("Error sending email:", e)

        return render(request, "otp.html")


@login_required(login_url='tplogin')
@user_passes_test(is_tp, login_url='tplogin')

@login_required 
def tpportal(request):
    announcements = Announcements.objects.all().order_by('-created_at')
    selected_year = request.GET.get('academic_year', '')

    invitations = CompanyInvitations.objects.filter(response='Willing to come to campus')
    invitations_pending = CompanyInvitations.objects.filter(response='Not responded')

    branch_synonyms = {'mech': 'mec'}  # normalization map

    # Get placed students (with student details)
    placed_regs = Registrations.objects.filter(result='placed').select_related('rollnumber')
    if selected_year:
        placed_regs = placed_regs.filter(rollnumber__academic_year=selected_year)

    # Find unique student branches dynamically
    branches = sorted({
        student.rollnumber.branch.strip().upper()
        for student in placed_regs
        if student.rollnumber and student.rollnumber.branch
    })

    # Initialize counts and per-student flags
    branch_counts = {branch: {'core': 0, 'non_core': 0, 'both': 0} for branch in branches}
    student_flags = {branch: {} for branch in branches}

    for reg in placed_regs:
        student = reg.rollnumber
        if not student or not student.branch:
            continue

        branch_raw = student.branch.strip().upper()
        branch_norm = student.branch.strip().lower()
        branch_norm = branch_synonyms.get(branch_norm, branch_norm)

        roll_no = student.roll_no
        student_flags[branch_raw].setdefault(roll_no, set())

        profiles = CompanyJobprofiles.objects.filter(company_id=reg.company_id)

        for profile in profiles:
            core = [
                branch_synonyms.get(b.strip().lower(), b.strip().lower())
                for b in (profile.eligible_core_branch or '').split(',')
                if b.strip()
            ]
            non_core = [
                branch_synonyms.get(b.strip().lower(), b.strip().lower())
                for b in (profile.eligible_non_core_branch or '').split(',')
                if b.strip()
            ]

            if branch_norm in core:
                student_flags[branch_raw][roll_no].add('core')

            if branch_norm in non_core:
                student_flags[branch_raw][roll_no].add('non-core')

    # Count students per branch based on flags
    for branch in branches:
        for offers in student_flags[branch].values():
            if 'core' in offers and 'non-core' in offers:
                branch_counts[branch]['both'] += 1
            elif 'core' in offers:
                branch_counts[branch]['core'] += 1
            elif 'non-core' in offers:
                branch_counts[branch]['non_core'] += 1

    # Prepare data for chart
    branch_labels, branch_data = [], []
    for branch in branches:
        counts = branch_counts[branch]
        total = counts['core'] + counts['non_core'] + counts['both']
        label = [f"{branch}", f"core:{counts['core']}", f"non-core:{counts['non_core']}", f"both:{counts['both']}"]
        branch_labels.append(label)
        branch_data.append(total)

    # Get distinct academic years for the filter dropdown
    academic_years = Student.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    return render(request, 'T&P_Dashboard.html', {
        'announcements':announcements,
        'total_count': invitations.count(),
        'pending_invitations': invitations_pending.count(),
        'branch_labels': json.dumps(branch_labels),
        'branch_data': json.dumps(branch_data),
        'academic_years': academic_years,
        'selected_year': selected_year,
    })

@login_required(login_url='tplogin')
@user_passes_test(is_tp_or_StuCoordinator, login_url='tplogin')
def verifystudents(request):
    if request.method=="POST":
        print(request.POST)
        if 'branch1' in request.POST:
            branch=request.POST['branch1']
            roll=request.POST['rollNumber']
            if branch!="nil" and roll=="":#through branch
                try:
                    students = Student.objects.filter(branch=branch,verified="No")
                    return render(request, "verifystudents.html", {'students': students})
                except Exception as e:
                    print(e)
                    messages.info(request,"All Students from this Branch are Verified.")
                    return render(request,"verifystudents.html")
            elif branch=="nil" and roll!="":#through rollno
                try :
                    student = Student.objects.get(roll_no=roll)
                    docs=Documents.objects.get(rollno=request.POST['rollNumber'])
                    return render(request, "verifystudents.html", {'student': student,'data':1,'docs':docs})
                except Exception as e:
                    print(e)
                    messages.info(request,"Enter Valid Credentials")
                    return render(request,"verifystudents.html")
            elif branch!="nil" and roll!="":#through both
                try :
                    student = Student.objects.get(roll_no=roll,branch=branch)
                    docs=Documents.objects.get(rollno=request.POST['rollNumber'])
                    return render(request, "verifystudents.html", {'student': student,'data':1,'docs':docs})
                except Exception as e:
                    messages.info(request,"Enter Valid Credentials")
                    return render(request,"verifystudents.html")
            else:
                messages.info(request,"Enter any one of the Feilds")
                return render(request,"verifystudents.html")
        elif 'rollNumber' in request.POST:
            student = Student.objects.get(roll_no=request.POST['rollNumber'])
            docs=Documents.objects.get(rollno=request.POST['rollNumber'])
            return render(request, "verifystudents.html", {'student': student,'data':1,'docs':docs})
        else:
            rollno = request.POST['rollno']
            cgpa = request.POST['cgpa']
            gate = request.POST['gate']
            backlogs = request.POST['backlogs']
            linkedin = request.POST['linkedin']
            verify = request.POST.get('verify', 'No')

            mssg = f"{cgpa} ; {gate} ; {backlogs} ; {linkedin} ;"
            student = Student.objects.get(roll_no=rollno)
            student.remarks = mssg
            if verify == "Yes":
                student.verified = "Yes"
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                docs = Documents.objects.get(rollno=rollno)

                file_path = extract_relative_path(docs.results)
                file_path2 = None
                d1=0
                d2=1
                if docs.scorecard and docs.scorecard != "null":
                    file_path2 = extract_relative_path(docs.scorecard)

                if file_path:
                    response = supabase.storage.from_("profile-pics").remove([file_path])
                    if isinstance(response, dict) and response.get("error"):
                        print("Error deleting file:", response["error"])
                    else:
                        d1=1
                        print("File deleted successfully")

                if file_path2:
                    response = supabase.storage.from_("profile-pics").remove([file_path2])
                    if isinstance(response, dict) and response.get("error"):
                        d2=0
                        print("Error deleting file:", response["error"])
                    else:
                        d2=1
                        print("Second file deleted successfully")
                if d1 and d2:
                    docs.delete()
                    print(f"Documents row for rollno {rollno} deleted.")

            student.save()
            return redirect("navigatetoindex")
                

    else:
        pendingStudents=Student.objects.filter(verified='No').count()
        return render(request,"verifystudents.html",{"pendingStudents":pendingStudents})

def displayStatus(request,reg,roll):
    send=[]
    # roll=request.POST['rollno']
    student=Student.objects.get(roll_no=roll)
    if student.registered=="Yes":
                try: 
                    register=Registrations.objects.get(registered_id__iexact=reg)
                    # for reg in register:
                    #     company=Company.objects.get(tbl_id=request.company_id)
                    #     ob={"companyName":company.name,"level":levelId[reg.level],"status":reg.status}
                    #     send.append(ob)
                    company=Company.objects.get(id=register.company_id)
                    ob={"companyName":company.name,"level":levelId[register.level],"status":register.status}
                    send.append(ob)
                except Exception as e:
                    print(e)
    print(send)
    return send

@login_required(login_url='tplogin')
@user_passes_test(is_tp, login_url='tplogin')
def updatestudentplacement(request):
    if request.method == "POST":
        # Handle CSV or XLSX upload
        if 'csvfile' in request.FILES:
            uploaded_file = request.FILES['csvfile']

            if uploaded_file.name.endswith('.csv'):
                try:
                    data_set = uploaded_file.read().decode('UTF-8')
                    io_string = io.StringIO(data_set)
                    reader = csv.DictReader(io_string)

                    for row in reader:
                        register = row.get('register')
                        status = row.get('status')
                        level = row.get('level')

                        try:
                            reg = Registrations.objects.get(registered_id=register)
                            reg.status = status
                            reg.level = level
                            reg.save()

                            stu = Student.objects.get(roll_no=reg.rollnumber)
                            recipient_email = "dummymailforme4321@gmail.com"  # replace with stu.email if needed
                            subject = 'Placement Status Updated'
                            message = f"""
Dear {stu.name},

Your placement status has been updated:
Status: {status}
Level: {level}
You can view your status by logging in to your portal.

Thank you

Regards,
Training and Placement Cell
"""
                            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=False)
                            Mails.objects.create(roll_no=reg.rollnumber, message=message)
                        except (Registrations.DoesNotExist, Student.DoesNotExist) as e:
                            print(f"Error for register ID {register}: {e}")
                            continue

                    messages.success(request, "CSV upload and update successful.")
                    return render(request, "update_student_placement.html", {"form2": 0})

                except Exception as e:
                    print("CSV processing error:", e)
                    messages.error(request, f"Error processing CSV: {e}")
                    return render(request, "update_student_placement.html")

            elif uploaded_file.name.endswith('.xlsx'):
                try:
                    wb = openpyxl.load_workbook(uploaded_file)
                    sheet = wb.active
                    headers = [cell.value for cell in sheet[1]]
                    headers = [str(cell.value).strip().lower() for cell in sheet[1]]
                    print("Headers found in Excel:", headers)

                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        row_data = dict(zip(headers, row))
                        register = row_data.get('registered_id')
                        status = row_data.get('status')
                        level = row_data.get('level')
                        try:
                            reg = Registrations.objects.get(registered_id=register)
                            reg.status = status
                            reg.level = level
                            reg.save()

                            stu = Student.objects.get(roll_no=reg.rollnumber)
                            recipient_email = "dummymailforme4321@gmail.com"
                            subject = 'Placement Status Updated'
                            message = f"""
Dear {stu.name},

Your placement status has been updated:
Status: {status}
Level: {level}
You can view your status by logging in to your portal.

Thank you

Regards,
Training and Placement Cell
"""
                            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=False)
                            Mails.objects.create(roll_no=reg.rollnumber, message=message)
                            messages.info(request,"For registered Id "+str(register)+" status has updated to"+status)
                        except (Registrations.DoesNotExist, Student.DoesNotExist) as e:
                            print(f"Error for register ID {register}: {e}")
                            continue

                    messages.success(request, "Excel upload and update successful.")
                    return render(request, "update_student_placement.html", {"form2": 0})

                except Exception as e:
                    print("Excel processing error:", e)
                    messages.error(request, f"Error processing Excel file: {e}")
                    return render(request, "update_student_placement.html")

            else:
                messages.error(request, "Unsupported file format. Please upload a CSV or Excel (.xlsx) file.")
                return render(request, "update_student_placement.html")

        # Handle single student form view
        elif 'status' not in request.POST:
            register = request.POST['register']
            student = Registrations.objects.get(registered_id=register)
            stu = Student.objects.get(roll_no=student.rollnumber)
            form2 = "yes"
            send = displayStatus(request, register, stu.roll_no)
            return render(request, "update_student_placement.html", {'student': student, 'form2': form2, 'send': send, 'stu': stu})

        # Handle single student manual update
        else:
            register = request.POST['register']
            status = request.POST['status']
            level = request.POST['level']
            registerStu = Registrations.objects.get(registered_id=register)
            student = Student.objects.get(roll_no=registerStu.rollnumber)
            registerStu.status = status
            registerStu.level = level
            registerStu.save()

            recipient_email = "dummymailforme4321@gmail.com"
            student_name = student.name

            subject = 'Placement Status Updated'
            message = f"""
Dear {student_name},

Your placement status has been updated:
Status: {status}
Level: {level}
You can view your status by logging in to your portal.

Thank you

Regards,
Training and Placement Cell
"""
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=False)
                Mails.objects.create(roll_no=registerStu.rollnumber, message=message)
            except Exception as e:
                print("Error sending email:", e)

            return render(request, "update_student_placement.html", {"form2": 0})

    return render(request, "update_student_placement.html")

def notifications(request):
    roll=request.user.username.split("@")[0]
    mails=Mails.objects.filter(roll_no=roll)
    send=[]
    for mail in mails:
        send.append(mail.message)
    return render(request,"notifications.html",{"send":send})

@login_required(login_url='login')
def stats(request):
    roll=request.user.username.split("@")[0]
    register=Registrations.objects.filter(rollnumber=roll)
    cv,apt,gd,ct,ti,hr,acc,rej=0,0,0,0,0,0,0,0
    app=register.count()
    companies=[]
    for reg in register:
        print("level",reg.level)
        if levelId[reg.level]>=2:
            cv=cv+1
        if levelId[reg.level]>=3:
            apt=apt+1
        if levelId[reg.level]>=4:
            gd=gd+1
        if levelId[reg.level]>=5:
            ct=ct+1
        if levelId[reg.level]>=6:
            ti=ti+1
        if levelId[reg.level]>=7:
            hr=hr+1
        if reg.status=="Accepted":
            acc=acc+1
        if reg.status=="Rejected":
            rej=rej+1
        if reg.status!="Accepted" and reg.status!="Rejected":
            comp=Company.objects.get(id=reg.company_id)
            companies.append(comp)
    if app!=0:
        percent=((app-acc-rej)/app)*100
    else:
        percent=0
    student={"Applied":app,"cv":cv,"apt":apt,"gd":gd,"ct":ct,"ti":ti,"hr":hr,"acc":acc,"rej":rej,"percent":percent,"companies":companies}
    print(student)
    return render(request,"stats.html",{"student":student})


@login_required(login_url='tplogin')
def editprofile(request):
    if request.method=="POST":
        roll=request.user.username.split("@")[0]
        student=Student.objects.get(roll_no=roll)
        student.name=request.POST['name']
        student.year=request.POST['year']
        student.email=request.POST['email']
        student.willing=request.POST['willing']
        student.mobile=request.POST['mobileNo']
        student.cgpa=request.POST['cgpa']
        student.gate=request.POST['gate']
        student.backlogs=request.POST['backlogs']
        student.interest=request.POST['job_interest_type']
        student.placed=request.POST['placed']
        student.linkedin=request.POST['linkedin']
        student.verified="No"
        student.remarks="Nil"
        student.save()
        return redirect('profile')

    else:
        return render(request,"editprofile.html")

def studentcoordinatorlogin(request):
    if request.method=="POST":
        email=request.POST['email']
        password=request.POST['password']
        user_type = UserType.objects.filter(id=email).first()
        if user_type and user_type.type == "StudentCoordinator":
            user=auth.authenticate(username=email,password=password)
            if user is not None :
                auth.login(request,user)
                return render(request,"studentCoordinator.html")
            else :
                messages.info(request,'Invalid Credentials !!!')
                return redirect("studentcoordinatorlogin")
        else :
            messages.info(request,'Invalid Credentials !!!')
            return redirect("login")
    return render(request,"studentCoordinatorLogin.html")

def studentcoordinatorverifystudents(request):
    user =  Student.objects.filter(roll_no=request.user.username.split('@')[0]).first()
    students=Student.objects.filter(verified="No", branch=user.branch)
    return render(request,'verifystudents.html',{"branch":user.branch,"pendingStudents":students.count(),"students":students})

@login_required(login_url='tplogin')
@user_passes_test(is_tp, login_url='tplogin')
def assignstudentcoordinator(request):
    if request.method=="POST":
        if 'change' in request.POST:
            rollNo=request.POST.get('rollNo')
            usrtype=UserType.objects.filter(id=rollNo+"@student.nitandhra.ac.in").first()
            if usrtype.type=="StudentCoordinator":
                usrtype.type="Student"
                usrtype.save()
                mssg="Sorry!! to Say that You have been demoted from Student Coordinator Position, Thanks For Your Continuous Effort"
            else:
                usrtype.type="StudentCoordinator"
                usrtype.save()
                mssg="Congratulations !! You have been appointed as the Student Coordinator for your Department. For more details contact T&P"
            subject="Update Regarding the Student Coordinator Position For Your Department"
            sendTo="dummymailforme4321@gmail.com"
            message=f"""
{mssg}
Best Regards,
Training and Placement Cell
National Institute of Technology Andhra Pradesh
"""
            send_mail(subject,message,settings.DEFAULT_FROM_EMAIL,recipient_list=[sendTo],fail_silently=False)
            return render(request,"assignstudentcoordinator.html")
        elif "branch" in request.POST:
            branch=request.POST.get('branch')
            branchid={"BIO":"1","CHE":"2","CIV":"3","CSE":"4","EEE":"5","ECE":"6","MEC":"7","MME":"8"}
            usrtype=UserType.objects.filter(type="StudentCoordinator")
            students=[]
            for usr in usrtype:
                if usr.id[0]==branchid[branch]:
                    roll=(usr.id.split('@')[0])
                    stu=Student.objects.filter(roll_no=roll).first()
                    student={"roll":roll,"name":stu.name}
                    students.append(student)
            return render(request,"assignstudentcoordinator.html",{"students":students})
        else:
            rollNo=request.POST['rollNumber']
            student=Student.objects.filter(roll_no=rollNo).first()
            usrtype=UserType.objects.filter(id=rollNo+"@student.nitandhra.ac.in").first()
            return render(request,"assignstudentcoordinator.html",{"rollNo":rollNo,"name":student.name,"branch":student.branch,"type":usrtype.type})
    
    return render(request,"assignstudentcoordinator.html")

def forgetpassword(request):
    if request.method=="POST":
        if "email" in request.POST:
            email=request.POST['email']
            otp=random.randint(1000,9999)
            request.session['otp']=otp
            request.session['email']=email
            subject="OTP for Changing Password"
            sendTo="dummymailforme4321@gmail.com"
            message=f"""
Dear Student,
    OTP for Changing the Password is {otp}. It is Valid for 15 min

Thank You.
Best Regards,
Training & Placement Cell
National Institute of Technology Andhra Pradesh
"""
            send_mail(subject,message,settings.DEFAULT_FROM_EMAIL,[sendTo],fail_silently=False)
            return render(request,"forgetPassword.html",{"otp":True})
        elif "otp" in request.POST:
            usr_otp=request.POST['otp']
            original_otp=request.session['otp']
            if int(usr_otp)==original_otp:
                return render(request,"forgetPassword.html",{"password":True})
            else:
                messages.error(request,"Enter Correct OTP")
                return render(request,"forgetPassword.html",{"otp":True})

        else:
            pwd1=request.POST['password1']
            pwd2=request.POST['password2']
            if pwd1!=pwd2:
                messages.error(request,"Both Passwords Should Match")
                return render(request,"forgetPassword.html",{"password":True})
            else:
                email=request.session['email']
                roll=email.split('@')[0]
                stu=Student.objects.filter(roll_no=roll).first()
                usr=User.objects.filter(username=email).first()
                usr.set_password(pwd1)
                usr.save()
                stu.password=pwd1
                stu.save()
                subject="Password Updated Successfully!!"
                sendTo="dummymailforme4321@gmail.com"
                message=f"""
Dear Student,
    Password Updated Successfully. Kindly Login using updated password.
Thank You.

Best Regards,
Training & Placement Cell,
National Institute of Technology Andhra Pradesh."""
                send_mail(subject,message,settings.DEFAULT_FROM_EMAIL,[sendTo],fail_silently=False)
                request.session.clear()
                return redirect("login")
    else:
        return render(request,"forgetPassword.html")

def navigatetoindex(request):
    print("userr",request.user)
    if isinstance(request.user, AnonymousUser):
        return redirect('index')
    else:
        user=UserType.objects.filter(id=request.user.username).first()
        if(user.type=="Student"):
            return redirect('index')
        elif(user.type=="StudentCoordinator"):
            return render(request,'studentcoordinator.html')
        else:
            return redirect('tpportal')
    
@login_required(login_url='tplogin')
@user_passes_test(is_tp, login_url='tplogin')
def addannouncements(request):
    if request.method=="POST":
        text=request.POST['text']
        document=request.FILES['document']
        # supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        #     # Profile picture
        #     filename = f"profilepics/{get_random_string(10)}_{profilepic.name}"
        #     upload_response = supabase.storage.from_('profile-pics').upload(filename, profilepic.read())
        supabase=create_client(settings.SUPABASE_URL,settings.SUPABASE_KEY)
        filename=f"announcements/{get_random_string(10)}_{document.name}"
        upload_response=supabase.storage.from_('profile-pics').upload(filename,document.read())
        if (upload_response):
            document_url=supabase.storage.from_('profile-pics').get_public_url(filename)
            announcement=Announcements.objects.create(text=text,document_url=document_url)
            announcement.save()
            messages.success(request,"New Announcement added")
            return redirect('navigatetoindex')
        else:
            messages.error(request,"Unable to add Announcement, Try Again later")
            return redirect('addannouncements')
    else:
        return render(request,'addannouncements.html')
    
def announcements(request):
    announcements=list(Announcements.objects.filter())
    return render(request,'announcements.html',{"announcements":announcements})

@login_required(login_url="login")
def registerforplacements(request):
    companies={}
    jobs=list(CompanyJobprofiles.objects.filter().order_by("-key"))
    for job in jobs:
        companies[job.key]={"comapanyname":list(Company.objects.filter(id=job.company_id)),"job":job,}
    return render(request,'registerforplacements.html',{"companies":companies})