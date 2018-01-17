# python-document-management

Prototype document management backend API using Python3, Django web framework and PostgreSQL.

API hosted using AWS Lambda, DB hosted on AWS RDS, continuous deployment via CircleCI.


## To start Django server locally:

1. Copy local_settings.py.dist to local_settings.py
    > `cp pydocman/pydocman/local_settings.py.dist pydocman/pydocman/local_settings.py`
2. Add `S3_BUCKET` variable in `local_settings.py`
3. Setup Python venv and packages
    > `python -m venv venv`
    > `pip install -r requirements.txt`
4. Run migrations
    > `python manage.py migrate`
5. Start server:
    > `python manage.py runserver 0.0.0.0:8080`

### Run tests locally:
    > `python manage.py test api.tests`

## Setting up AWS credentials:

1. Install AWS CLI
    > `pip install awscli`
2. Set up AWS access id and secret key
    > `aws configure`
3. Required permissions for deployment to AWS Lambda via `zappa`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:AttachRolePolicy",
                "iam:CreateRole",
                "iam:GetRole",
                "iam:PutRolePolicy"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::<account_id>:role/*-ZappaLambdaExecutionRole"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:DELETE",
                "apigateway:GET",
                "apigateway:PATCH",
                "apigateway:POST",
                "apigateway:PUT",
                "events:DeleteRule",
                "events:DescribeRule",
                "events:ListRules",
                "events:ListTargetsByRule",
                "events:ListRuleNamesByTarget",
                "events:PutRule",
                "events:PutTargets",
                "events:RemoveTargets",
                "lambda:AddPermission",
                "lambda:CreateFunction",
                "lambda:DeleteFunction",
                "lambda:GetFunction",
                "lambda:GetFunctionConfiguration",
                "lambda:GetPolicy",
                "lambda:ListVersionsByFunction",
                "lambda:RemovePermission",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "cloudformation:CreateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStackResource",
                "cloudformation:DescribeStacks",
                "cloudformation:ListStackResources",
                "cloudformation:UpdateStack",
                "logs:DescribeLogStreams",
                "logs:FilterLogEvents",
                "route53:ListHostedZones",
                "route53:ChangeResourceRecordSets",
                "route53:GetHostedZone",
                "s3:CreateBucket"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::<s3_bucket_name>"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:PutObject",
                "s3:CreateMultipartUpload",
                "s3:AbortMultipartUpload",
                "s3:ListMultipartUploadParts",
                "s3:ListBucketMultipartUploads"
            ],
            "Resource": [
                "arn:aws:s3:::<s3_bucket_name>/*"
            ]
        }
    ]
}
```
## Deployment
Setup up environmental variables on AWS Lambda _after_ initial deployment:
* DB_NAME, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT
* DJANGO_SECRET_KEY : Generate random 50 letter alphanumeric string

### Deployment with CircleCI
CircleCI configuration YAML file is included. Setup CircleCI to track repository.
Commits on branch `staging` will be deployed according to `demo` in `zappa_settings.json`,
and commits on `master` will be deployed to `live`.

### Manual deployment
Initial deployment:

    zappa deploy <demo/live>

Later deployments:

    zappa update <demo/live>

### Model migration
Whenever the `models.py` file is updated, Django can generate the migrations using

    python manage.py makemigrations
    
Then to propagate the migrations:

    python manage.py migrate

### Data migration

Data migrations are easily done through Python scripts ran using Django's shell.
Django's interactive shell can be run using `python manage.py shell`.

1. Setting up a lender, permission groups and users
```python
from api.models import Lender
from django.contrib.auth.models import User, Group, Permission
# Lender
l = Lender.objects.create(name='Test Lender')

# Permissions
read_permission = Permission.objects.get(codename='read_document')
draft_permission = Permission.objects.get(codename='draft_document')
publish_permission = Permission.objects.get(codename='publish_document')
create_document_type_permission = Permission.objects.get(codename='create_lender_document')

# Permission Groups
r_group = Group.objects.create(name='Test Lender Readers')
r_group.permissions.add(read_permission)
r_group.save()

rd_group = Group.objects.create(name='Test Lender Drafters')
rd_group.permissions.add(read_permission, draft_permission)
rd_group.save()

rdp_group = Group.objects.create(name='Test Lender Publishers')
rdp_group.permissions.add(read_permission, draft_permission, publish_permission)
rdp_group.save()

ld_group = Group.objects.create(name='Test Lender Document Type Managers')
ld_group.permissions.add(create_document_type_permission)
ld_group.save()

# Users
u = User.objects.create_user(username='testuser1', password='testuser1')
u.profile.lender = l
u.groups.add(rdp_group, ld_group)
u.save()

# Checking for permissions:
u.has_perm('api.read_document') # <app label>.<permission codename>
```

2. Setting up lender document types:
```python
from api.models import Lender, LenderDocument
l, created = Lender.objects.get_or_create(name='Test Lender')
ld_type = LenderDocument.objects.create(name='Terms of Service', lender=l)
```

### API Documentation
[Postman documentation](https://documenter.getpostman.com/view/3474948/pydocman/7Lt5eX5)
