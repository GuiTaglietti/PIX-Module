# db/postgres.py
# https://www.devmedia.com.br/como-criar-uma-conexao-em-postgresql-com-python/34079
import psycopg2

con = psycopg2.connect(host='localhost', database='test',
                       user='postgres', password='postgres123')

cur = con.cursor()

#sql = 'CREATE TABLE cidade (id SERIAL PRIMARY KEY, nome VARCHAR(50), uf VARCHAR(2))'
#cur.execute(sql)

sql = "INSERT INTO cidade VALUES (default, 'Sarandi', 'RS')"
cur.execute(sql)

con.commit()

cur.execute('SELECT * FROM cidade')

recset = cur.fetchall()

for rec in recset:
    print(rec)

con.close()

