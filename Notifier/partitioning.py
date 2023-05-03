from dateutil.relativedelta import relativedelta
from nf_core.models import UserRechargeHistory, SMSHistory

from psqlextra.partitioning import (
    PostgresPartitioningManager,
    PostgresCurrentTimePartitioningStrategy,
    PostgresTimePartitionSize,
    partition_by_current_time,
)
from psqlextra.partitioning.config import PostgresPartitioningConfig

manager = PostgresPartitioningManager([
    # 1 partitions ahead, each partition is one weeks
    # partitions will be named `[table_name]_[year]_week_[week number]`.
    PostgresPartitioningConfig(
        model=UserRechargeHistory,
        strategy=PostgresCurrentTimePartitioningStrategy(
            size=PostgresTimePartitionSize(weeks=1),
            count=1
        ),
    ),
    # 1 partitions ahead, each partition is one weeks
    # partitions will be named `[table_name]_[year]_week_[week number]`.
    PostgresPartitioningConfig(
        model=SMSHistory,
        strategy=PostgresCurrentTimePartitioningStrategy(
            size=PostgresTimePartitionSize(weeks=1),
            count=1
        ),
    ),
])
