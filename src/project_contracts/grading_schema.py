from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GradingBucket(ContractBaseModel):
    name: str
    event_ids: list[int] = Field(min_length=1)
    count_correct_for_full_credit: int = Field(ge=1)
    count_correct_for_partial_credit: int = Field(ge=0)
    grade_points_for_bucket: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "GradingBucket":
        event_count = len(self.event_ids)

        if len(set(self.event_ids)) != event_count:
            raise ValueError("event_ids must not contain duplicates within a bucket")

        if self.count_correct_for_full_credit > event_count:
            raise ValueError(
                "count_correct_for_full_credit must be less than or equal to the number of event_ids"
            )

        if self.count_correct_for_partial_credit > self.count_correct_for_full_credit:
            raise ValueError(
                "count_correct_for_partial_credit must be less than or equal to count_correct_for_full_credit"
            )

        return self


class GradingSchema(ContractBaseModel):
    buckets: list[GradingBucket] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_bucket_event_ids_do_not_overlap(self) -> "GradingSchema":
        seen: set[int] = set()

        for bucket in self.buckets:
            overlap = seen.intersection(bucket.event_ids)
            if overlap:
                raise ValueError(
                    f"event_ids appear in multiple buckets: {sorted(overlap)}"
                )
            seen.update(bucket.event_ids)

        return self
