# AWS S3 Image Resizer

Upload an image to one S3 bucket and a Lambda function automatically writes a 256x256 (aspect-preserving) thumbnail to a second bucket. Built with AWS SAM and Pillow.

## Architecture

```
  upload .jpg/.jpeg/.png
          |
          v
  [ Source bucket ] --ObjectCreated--> [ Lambda (Python + Pillow) ] --> [ Thumbnail bucket ]
```

**Why two buckets?** If the Lambda wrote thumbnails back into the source bucket, each new thumbnail would trigger the function again, creating an infinite loop (and a surprise bill). A separate output bucket prevents that.

## Features
- Triggers on `.jpg`, `.jpeg`, `.png` uploads
- Fixes EXIF rotation on phone photos
- Preserves aspect ratio and original format
- Least-privilege IAM: read from source, write to thumbs only

## Cost: $0 at demo scale
| Service | Free tier |
|---|---|
| Lambda | 1M requests + 400,000 GB-seconds per month (always free) |
| S3 | 5 GB storage for the first 12 months |
| CloudWatch Logs | 5 GB ingestion per month |

Check current AWS Free Tier terms, as they can change.

## Prerequisites
- AWS account and CLI configured (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- Docker (for `sam build --use-container`, which builds Pillow for Lambda's Linux runtime)

## Deploy
```bash
sam build --use-container
sam deploy --guided --stack-name image-resizer
```
Use a lowercase stack name, since it becomes part of the bucket names.

## Try it
```bash
aws s3 cp photo.jpg s3://image-resizer-source-<ACCOUNT_ID>/
aws s3 ls s3://image-resizer-thumbs-<ACCOUNT_ID>/
aws s3 cp s3://image-resizer-thumbs-<ACCOUNT_ID>/thumb-photo.jpg .
```

## Clean up
```bash
aws s3 rm s3://image-resizer-source-<ACCOUNT_ID> --recursive
aws s3 rm s3://image-resizer-thumbs-<ACCOUNT_ID> --recursive
sam delete --stack-name image-resizer
```

## CI/CD with GitHub Actions (OIDC, no stored keys)
`.github/workflows/deploy.yml` deploys on every push to `main`.

1. In AWS IAM, add an **OIDC identity provider**: URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
2. Create an IAM role with a trust policy limited to your repo:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": {"Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"},
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
         "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
         "StringLike": {"token.actions.githubusercontent.com:sub": "repo:<GITHUB_USER>/<REPO>:ref:refs/heads/main"}
       }
     }]
   }
   ```
3. Attach permissions the role needs to deploy (CloudFormation, Lambda, S3, IAM role creation, and so on). Start broad for a personal sandbox, then tighten.
4. In the GitHub repo: **Settings > Secrets and variables > Actions**, add secret `AWS_ROLE_ARN` (and optionally variable `AWS_REGION`).

## Ideas for extension
- Multiple sizes (small / medium / large)
- Store image metadata in DynamoDB
- SNS or email notification when a thumbnail is ready
- Add a before/after screenshot to this README

## License
MIT
