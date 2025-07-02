from rest_framework import serializers
from MainInterface.models import Company, CompanyJobprofiles

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class CompanyJobprofileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyJobprofiles
        fields = '__all__'

class CompanyWithProfilesSerializer(serializers.ModelSerializer):
    jobprofiles = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'

    def get_jobprofiles(self, obj):
        profiles = CompanyJobprofiles.objects.filter(company=obj)
        return CompanyJobprofileSerializer(profiles, many=True).data
