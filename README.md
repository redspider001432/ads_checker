# ats_checker

<img width="1423" alt="image" src="https://github.com/user-attachments/assets/72bca477-0010-407d-9cf0-1b8c48b0eca6" />

# GOAL

```
graph TD
    A[Resume File] --> B[.get_file() - Parsing]
    B --> C[ATS Scoring - Keyword/Vector Analysis]
    C --> D[.get_email() - Notify High Scores]
    C --> E[.get_keys() - Store in AWS S3/SQS]
```
