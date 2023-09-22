from peewee import CharField, PostgresqlDatabase
from playhouse.migrate import migrate, PostgresqlMigrator

# PostgreSQL credentials
HOST = "localhost"
PORT = 5432
USER = "postgres"
PASSWORD = "postgres"
DATABASE_NAME = "messenger".lower()

db = PostgresqlDatabase(DATABASE_NAME, host = HOST,  port = PORT, user = USER, password = PASSWORD)
migrator = PostgresqlMigrator(db)

new_field = CharField(default = "empty")

# add_column, drop_column, rename_column, rename_table, add_index, drop_index...

migrate(
	migrator.add_column("Users", "new_column1", new_field)
	#migrator.drop_column("Users", "new_column")
)
