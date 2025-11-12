"""
Helper functions for recording data lineage.

Provides simple, consistent API for recording lineage during manual entry
or automated data extraction. Ensures all data points have complete
provenance tracking.
"""

from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from src.database.models.core import DataLineage, DataSource

logger = structlog.get_logger(__name__)


class LineageRecorder:
    """
    Helper class for recording data lineage.

    Makes it easy to record lineage during data entry operations.
    Ensures consistent, complete lineage tracking across all data points.
    """

    def __init__(self, db: Session):
        """Initialize recorder with database session."""
        self.db = db

    def record_manual_entry(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        source_id: int,
        extracted_by: str,
        source_document_url: Optional[str] = None,
        source_document_page: Optional[int] = None,
        source_document_section: Optional[str] = None,
        source_document_table_name: Optional[str] = None,
        source_document_line_item: Optional[str] = None,
        notes: Optional[str] = None,
        confidence_score: int = 100,
        confidence_level: str = "High",
    ) -> DataLineage:
        """
        Record lineage for manually entered data.

        Manual entry gets 100% confidence by default since a human
        transcribed it directly from the source document.

        Args:
            table_name: Database table name
            record_id: Record ID
            field_name: Field name
            source_id: ID of source document in data_sources table
            extracted_by: Name/email of person who entered the data
            source_document_url: URL to source document
            source_document_page: Page number in source document
            source_document_section: Section name (e.g., "Statement of Activities")
            source_document_table_name: Table name in source (e.g., "Table 5")
            source_document_line_item: Specific line item (e.g., "Line 42")
            notes: Additional notes about the data entry
            confidence_score: Confidence 0-100 (default 100 for manual entry)
            confidence_level: High/Medium/Low (default High for manual entry)

        Returns:
            Created DataLineage record
        """
        lineage = DataLineage(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            source_id=source_id,
            source_document_url=source_document_url,
            source_document_page=source_document_page,
            source_document_section=source_document_section,
            source_document_table_name=source_document_table_name,
            source_document_line_item=source_document_line_item,
            extraction_method="Manual",
            extracted_by=extracted_by,
            extracted_at=datetime.utcnow(),
            validated=False,  # Not yet validated
            notes=notes,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
        )

        self.db.add(lineage)
        self.db.commit()

        logger.info(
            "lineage_recorded",
            table=table_name,
            record_id=record_id,
            field=field_name,
            method="Manual",
            by=extracted_by,
        )

        return lineage

    def validate_lineage(
        self,
        lineage_id: int,
        validated_by: str,
        validation_notes: Optional[str] = None,
        cross_validated_source_id: Optional[int] = None,
        matches_cross_validation: Optional[bool] = None,
    ) -> DataLineage:
        """
        Mark a lineage record as validated.

        Args:
            lineage_id: ID of lineage record to validate
            validated_by: Name/email of validator
            validation_notes: Notes from validation
            cross_validated_source_id: Optional second source for cross-validation
            matches_cross_validation: Does it match the second source?

        Returns:
            Updated DataLineage record
        """
        lineage = self.db.query(DataLineage).filter(DataLineage.id == lineage_id).first()

        if not lineage:
            raise ValueError(f"Lineage record {lineage_id} not found")

        lineage.validated = True
        lineage.validated_by = validated_by
        lineage.validated_at = datetime.utcnow()
        lineage.validation_notes = validation_notes

        if cross_validated_source_id:
            lineage.cross_validated_source_id = cross_validated_source_id
            lineage.matches_cross_validation = matches_cross_validation

        self.db.commit()

        logger.info(
            "lineage_validated",
            lineage_id=lineage_id,
            table=lineage.table_name,
            record_id=lineage.record_id,
            field=lineage.field_name,
            by=validated_by,
        )

        return lineage

    def record_automated_extraction(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        source_id: int,
        extraction_system: str,
        source_document_url: Optional[str] = None,
        source_document_page: Optional[int] = None,
        confidence_score: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> DataLineage:
        """
        Record lineage for automated data extraction.

        Automated extraction typically has lower confidence (85-95%)
        compared to manual entry (100%).

        Args:
            table_name: Database table name
            record_id: Record ID
            field_name: Field name
            source_id: ID of source document
            extraction_system: Name of extraction system (e.g., "PDF_Extractor_v1")
            source_document_url: URL to source document
            source_document_page: Page number
            confidence_score: Confidence 0-100
            notes: Additional notes

        Returns:
            Created DataLineage record
        """
        lineage = DataLineage(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            source_id=source_id,
            source_document_url=source_document_url,
            source_document_page=source_document_page,
            extraction_method="Automated",
            extracted_by=extraction_system,
            extracted_at=datetime.utcnow(),
            validated=False,
            notes=notes,
            confidence_score=confidence_score or 90,  # Default 90% for automation
            confidence_level="Medium" if (confidence_score or 90) < 95 else "High",
        )

        self.db.add(lineage)
        self.db.commit()

        logger.info(
            "lineage_recorded",
            table=table_name,
            record_id=record_id,
            field=field_name,
            method="Automated",
            system=extraction_system,
        )

        return lineage

    def record_calculated_field(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        calculation_method: str,
        calculated_by: str,
        notes: Optional[str] = None,
        confidence_score: int = 100,
    ) -> DataLineage:
        """
        Record lineage for calculated/derived fields.

        For fields that are calculated from other fields rather than
        directly extracted from source documents.

        Args:
            table_name: Database table name
            record_id: Record ID
            field_name: Field name
            calculation_method: Description of calculation
            calculated_by: System or person who performed calculation
            notes: Additional notes
            confidence_score: Confidence in calculation (default 100%)

        Returns:
            Created DataLineage record
        """
        # Create or get a "Calculated" data source
        calculated_source = (
            self.db.query(DataSource)
            .filter(DataSource.name == "Calculated")
            .first()
        )

        if not calculated_source:
            calculated_source = DataSource(
                name="Calculated",
                source_type="Calculated",
                organization="IBCo",
                description="Derived/calculated fields from other data points",
                access_method="Calculation",
                reliability_rating="High",
            )
            self.db.add(calculated_source)
            self.db.commit()

        lineage = DataLineage(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            source_id=calculated_source.id,
            extraction_method="Calculated",
            extracted_by=calculated_by,
            extracted_at=datetime.utcnow(),
            validated=True,  # Calculations are automatically validated
            validated_by=calculated_by,
            validated_at=datetime.utcnow(),
            notes=notes or calculation_method,
            confidence_score=confidence_score,
            confidence_level="High" if confidence_score >= 95 else "Medium",
        )

        self.db.add(lineage)
        self.db.commit()

        logger.info(
            "lineage_recorded",
            table=table_name,
            record_id=record_id,
            field=field_name,
            method="Calculated",
        )

        return lineage

    def bulk_record_manual_entry(
        self,
        table_name: str,
        record_id: int,
        field_mappings: dict,
        source_id: int,
        extracted_by: str,
        source_document_url: Optional[str] = None,
        source_document_page: Optional[int] = None,
        source_document_table_name: Optional[str] = None,
    ) -> list[DataLineage]:
        """
        Record lineage for multiple fields at once (bulk operation).

        Useful when entering multiple fields from the same source location.

        Args:
            table_name: Database table name
            record_id: Record ID
            field_mappings: Dict of field_name -> notes
            source_id: ID of source document
            extracted_by: Name/email of person who entered the data
            source_document_url: URL to source document
            source_document_page: Page number
            source_document_table_name: Table name in source

        Returns:
            List of created DataLineage records
        """
        lineage_records = []

        for field_name, notes in field_mappings.items():
            lineage = self.record_manual_entry(
                table_name=table_name,
                record_id=record_id,
                field_name=field_name,
                source_id=source_id,
                extracted_by=extracted_by,
                source_document_url=source_document_url,
                source_document_page=source_document_page,
                source_document_table_name=source_document_table_name,
                notes=notes,
            )
            lineage_records.append(lineage)

        logger.info(
            "bulk_lineage_recorded",
            table=table_name,
            record_id=record_id,
            field_count=len(field_mappings),
            by=extracted_by,
        )

        return lineage_records


# Convenience functions for common operations


def record_cafr_entry(
    db: Session,
    table_name: str,
    record_id: int,
    field_name: str,
    cafr_source_id: int,
    page_number: int,
    section_name: str,
    entered_by: str,
    notes: Optional[str] = None,
) -> DataLineage:
    """
    Convenience function for recording CAFR manual entry.

    Args:
        db: Database session
        table_name: Table name
        record_id: Record ID
        field_name: Field name
        cafr_source_id: ID of CAFR data source
        page_number: CAFR page number
        section_name: CAFR section (e.g., "Statement of Activities")
        entered_by: Person who entered data
        notes: Optional notes

    Returns:
        Created DataLineage record
    """
    recorder = LineageRecorder(db)
    return recorder.record_manual_entry(
        table_name=table_name,
        record_id=record_id,
        field_name=field_name,
        source_id=cafr_source_id,
        extracted_by=entered_by,
        source_document_page=page_number,
        source_document_section=section_name,
        notes=notes,
        confidence_score=100,
        confidence_level="High",
    )


def record_calpers_entry(
    db: Session,
    table_name: str,
    record_id: int,
    field_name: str,
    calpers_source_id: int,
    page_number: int,
    table_name_in_doc: str,
    entered_by: str,
    notes: Optional[str] = None,
) -> DataLineage:
    """
    Convenience function for recording CalPERS manual entry.

    Args:
        db: Database session
        table_name: Table name
        record_id: Record ID
        field_name: Field name
        calpers_source_id: ID of CalPERS data source
        page_number: Page number in CalPERS valuation
        table_name_in_doc: Table name in the document (e.g., "Table 5")
        entered_by: Person who entered data
        notes: Optional notes

    Returns:
        Created DataLineage record
    """
    recorder = LineageRecorder(db)
    return recorder.record_manual_entry(
        table_name=table_name,
        record_id=record_id,
        field_name=field_name,
        source_id=calpers_source_id,
        extracted_by=entered_by,
        source_document_page=page_number,
        source_document_section="Actuarial Valuation",
        source_document_table_name=table_name_in_doc,
        notes=notes,
        confidence_score=100,
        confidence_level="High",
    )
