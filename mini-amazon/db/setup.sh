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

# python3 gen.py
# psql -af load.sql $dbname

# rm -f Carts.csv
# rm -f FeedbackProduct.csv
# rm -f FeedbackSeller.csv
# rm -f LineItems.csv
# rm -f Orders.csv
# rm -f Products.csv
# rm -f ProductSeller.csv
# rm -f Users.csv

echo "All temp fake data files removed."

