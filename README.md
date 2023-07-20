

# Connecting to DB

```sh
source .env
PGPASSWORD=$DB_PASSWORD
psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME $DB_DATABASE
```
