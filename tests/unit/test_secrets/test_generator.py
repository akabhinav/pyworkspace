from pyworkspace.secrets.generator import CredentialGenerator


class TestCredentialGenerator:
    def test_default(self):
        creds = CredentialGenerator.generate("unknown_service")
        assert "user" in creds
        assert "password" in creds

    def test_postgres(self):
        creds = CredentialGenerator.generate("postgres")
        assert "user" in creds
        assert "password" in creds
        assert "database" in creds
        assert creds["database"] == "pyws_db"

    def test_postgres_custom_db(self):
        creds = CredentialGenerator.generate("postgres", {"db": "mydb"})
        assert creds["database"] == "mydb"

    def test_mysql(self):
        creds = CredentialGenerator.generate("mysql")
        assert "root_password" in creds
        assert "user" in creds

    def test_mongodb(self):
        creds = CredentialGenerator.generate("mongodb")
        assert "database" in creds

    def test_redis(self):
        creds = CredentialGenerator.generate("redis")
        assert "password" in creds
        assert "user" not in creds

    def test_redis_cache(self):
        creds = CredentialGenerator.generate("redis_cache")
        assert "password" in creds

    def test_kafka(self):
        creds = CredentialGenerator.generate("kafka")
        assert "username" in creds
        assert creds["sasl_mechanism"] == "SCRAM-SHA-256"

    def test_rabbitmq(self):
        creds = CredentialGenerator.generate("rabbitmq")
        assert "user" in creds
        assert creds["vhost"] == "/"

    def test_elasticsearch(self):
        creds = CredentialGenerator.generate("elasticsearch")
        assert creds["user"] == "elastic"

    def test_neo4j(self):
        creds = CredentialGenerator.generate("neo4j")
        assert creds["user"] == "neo4j"

    def test_grafana(self):
        creds = CredentialGenerator.generate("grafana")
        assert creds["user"] == "admin"

    def test_jupyter(self):
        creds = CredentialGenerator.generate("jupyter")
        assert "token" in creds

    def test_minio(self):
        creds = CredentialGenerator.generate("minio")
        assert "access_key" in creds
        assert "secret_key" in creds

    def test_localstack(self):
        creds = CredentialGenerator.generate("localstack")
        assert creds["access_key"] == "localstack"

    def test_unique_passwords(self):
        c1 = CredentialGenerator.generate("postgres")
        c2 = CredentialGenerator.generate("postgres")
        assert c1["password"] != c2["password"]
