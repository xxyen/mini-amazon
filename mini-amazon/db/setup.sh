#!/bin/bash

mypath=`realpath "$0"`
mybase=`dirname "$mypath"`
cd $mybase

source ../.flaskenv
dbname=$DB_NAME

if [[ -n `psql -U postgres -lqt | cut -d \| -f 1 | grep -w "$dbname"` ]]; then
    dropdb -U postgres "$dbname"
fi
createdb -U postgres "$dbname"

psql -U postgres -af create.sql "$dbname"

python3 gendata.py
psql  -U postgres -af loaddata.sql $dbname

rm -f carts.csv
rm -f feedback_products.csv
# rm -f FeedbackSeller.csv
rm -f line_items.csv
rm -f orders.csv
rm -f products.csv
# rm -f ProductSeller.csv
rm -f users.csv
rm -f warehouses.csv
rm -f ups.csv

echo "All temp fake data files removed."

