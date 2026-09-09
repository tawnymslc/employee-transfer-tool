from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func, relationship

from database import Base

# migration run class, migration run table in the db
class MigrationRun(Base):
    __tablename__ = "migration_runs" #table
    __table_args__ = {"schema": "employee_transfer"} #schema 

    id = Column(BigInteger, primary_key=True)

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="running"
    )

    total_employees = Column(Integer, nullable=False, default=0)
    transferred_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)

    results = relationship(
        "MigrationResult",
        back_populates="migration_run"

)

# migration result class, migration run table in the db
class MigrationResult(Base):
    __tablename__ = "migration_results" #table
    __table_args__ = {"schema": "employee_transfer"} 

    id = Column(BigInteger, primary_key=True)

    migration_run_id = Column(
        BigInteger,
        ForeignKey("employee_transfer.migration_runs.id"),
        nullable=False
    )

    employee_id = Column(String(100), nullable=False)
    employee_name = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False)
    reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    migration_run = relationship(
        "MigrationRun",
        back_populates="results"

    )

    class LocationMapping(Base):
        __tablename__ = "location_mappings"
        __table_args__ = {"schema": "employee_transfer"}

        id = Column(BigInteger, primary_key=True)
        source_location = Column(String(200), nullable=False, unique=True)
        destination_location = Column(String(200), nullable=False)

        created_at = Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now()
        )

        updated_at = Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now()
        )


class PositionMapping(Base):
    __tablename__ = "position_mappings"
    __table_args__ = {"schema": "employee_transfer"}

    id = Column(BigInteger, primary_key=True)
    source_position = Column(String(200), nullable=False, unique=True)
    destination_position = Column(String(200), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )