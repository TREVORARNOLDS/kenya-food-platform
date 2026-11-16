CREATE DATABASE kfs_test;
\connect kfs_dev
CREATE EXTENSION IF NOT EXISTS postgis;
\connect kfs_test
CREATE EXTENSION IF NOT EXISTS postgis;