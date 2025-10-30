"""
Person API endpoints.

Provides CRUD operations and person-related functionality.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from backend.api.dependencies import get_person_service, require_auth
from backend.api.schemas import PersonCreate, PersonResponse, PersonStatistics, PersonUpdate
from backend.core.models import Date, Person
from backend.services.person_service import PersonService

router = APIRouter()


# ============================================================================
# Helper functions
# ============================================================================


def person_to_response(person: Person) -> PersonResponse:
    """
    Convert Person model to PersonResponse schema.

    Args:
        person: Person model instance.

    Returns:
        PersonResponse schema.
    """
    from backend.api.schemas.common import DateSchema, EventSchema

    def date_to_schema(date: Optional[Date]) -> Optional[DateSchema]:
        if date is None:
            return None
        return DateSchema(
            year=date.year,
            month=date.month,
            day=date.day,
            calendar=date.calendar,
        )

    return PersonResponse(
        id=person.id,
        first_name=person.first_name,
        surname=person.surname,
        sex=person.sex,
        birth_date=date_to_schema(person.birth_date),
        birth_place=person.birth_place,
        death_date=date_to_schema(person.death_date),
        death_place=person.death_place,
        occupation=person.occupation,
        public_name=person.public_name,
        aliases=person.aliases,
        titles=person.titles,
        family_id=person.family_id,
        family_ids=person.family_ids,
        events=[
            EventSchema(
                event_type=event.event_type,
                date=date_to_schema(event.date),
                place=event.place,
                note=event.note,
            )
            for event in person.events
        ],
        access_level=person.access_level,
    )


# ============================================================================
# CRUD Endpoints
# ============================================================================


@router.get("", response_model=List[PersonResponse])
async def list_persons(
    skip: int = Query(0, ge=0, description="Number of persons to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of persons to return"),
    service: PersonService = Depends(get_person_service),
) -> List[PersonResponse]:
    """
    List all persons with pagination.

    Args:
        skip: Number of persons to skip (offset).
        limit: Maximum number of persons to return.
        service: PersonService dependency.

    Returns:
        List of persons.

    Examples:
        >>> GET /api/persons?skip=0&limit=50
        [
            {
                "id": "P001",
                "first_name": "John",
                "surname": "Doe",
                ...
            }
        ]
    """
    # Get all persons from repository
    all_persons_dict = service.repository.get_all_persons()
    all_persons = list(all_persons_dict.values())
    paginated = all_persons[skip : skip + limit]
    return [person_to_response(p) for p in paginated]


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    service: PersonService = Depends(get_person_service),
    user: dict = Depends(require_auth),
) -> PersonResponse:
    """
    Create a new person.

    Args:
        person_data: Person creation data.
        service: PersonService dependency.
        user: Authenticated user (required).

    Returns:
        Created person.

    Raises:
        ValidationError: If data is invalid.
        HTTP 401: If not authenticated.

    Examples:
        >>> POST /api/persons
        >>> {
        >>>     "first_name": "John",
        >>>     "surname": "Doe",
        >>>     "sex": "M",
        >>>     "birth_date": {"year": 1990, "month": 5, "day": 15}
        >>> }
    """
    # Convert schema to Date objects if provided
    birth_date = None
    if person_data.birth_date:
        birth_date = Date(
            year=person_data.birth_date.year,
            month=person_data.birth_date.month,
            day=person_data.birth_date.day,
            calendar=person_data.birth_date.calendar,
        )

    death_date = None
    if person_data.death_date:
        death_date = Date(
            year=person_data.death_date.year,
            month=person_data.death_date.month,
            day=person_data.death_date.day,
            calendar=person_data.death_date.calendar,
        )

    # Create person
    person = service.create_person(
        first_name=person_data.first_name,
        surname=person_data.surname,
        sex=person_data.sex,
        birth_date=birth_date,
        birth_place=person_data.birth_place,
        death_date=death_date,
        death_place=person_data.death_place,
        occupation=person_data.occupation,
        public_name=person_data.public_name,
        aliases=person_data.aliases,
        titles=person_data.titles,
        access_level=person_data.access_level,
    )

    return person_to_response(person)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: str = Path(..., description="Person ID"),
    service: PersonService = Depends(get_person_service),
) -> PersonResponse:
    """
    Get a person by ID.

    Args:
        person_id: Person ID.
        service: PersonService dependency.

    Returns:
        Person details.

    Raises:
        HTTP 404: If person not found.

    Examples:
        >>> GET /api/persons/P001
        {
            "id": "P001",
            "first_name": "John",
            ...
        }
    """
    person = service.repository.get_person(person_id)
    return person_to_response(person)


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: str = Path(..., description="Person ID"),
    person_data: PersonUpdate = ...,
    service: PersonService = Depends(get_person_service),
    user: dict = Depends(require_auth),
) -> PersonResponse:
    """
    Update a person.

    Args:
        person_id: Person ID.
        person_data: Updated person data.
        service: PersonService dependency.
        user: Authenticated user (required).

    Returns:
        Updated person.

    Raises:
        HTTP 404: If person not found.
        HTTP 401: If not authenticated.

    Examples:
        >>> PUT /api/persons/P001
        >>> {
        >>>     "first_name": "Jane",
        >>>     "occupation": "Doctor"
        >>> }
    """
    # Build kwargs with only provided fields
    kwargs: Dict[str, Any] = {}

    if person_data.first_name is not None:
        kwargs["first_name"] = person_data.first_name
    if person_data.surname is not None:
        kwargs["surname"] = person_data.surname
    if person_data.sex is not None:
        kwargs["sex"] = person_data.sex
    if person_data.birth_date is not None:
        kwargs["birth_date"] = Date(
            year=person_data.birth_date.year,
            month=person_data.birth_date.month,
            day=person_data.birth_date.day,
            calendar=person_data.birth_date.calendar,
        )
    if person_data.birth_place is not None:
        kwargs["birth_place"] = person_data.birth_place
    if person_data.death_date is not None:
        kwargs["death_date"] = Date(
            year=person_data.death_date.year,
            month=person_data.death_date.month,
            day=person_data.death_date.day,
            calendar=person_data.death_date.calendar,
        )
    if person_data.death_place is not None:
        kwargs["death_place"] = person_data.death_place
    if person_data.occupation is not None:
        kwargs["occupation"] = person_data.occupation
    if person_data.public_name is not None:
        kwargs["public_name"] = person_data.public_name
    if person_data.access_level is not None:
        kwargs["access_level"] = person_data.access_level

    person = service.update_person(person_id, **kwargs)
    return person_to_response(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str = Path(..., description="Person ID"),
    service: PersonService = Depends(get_person_service),
    user: dict = Depends(require_auth),
) -> None:
    """
    Delete a person.

    Args:
        person_id: Person ID.
        service: PersonService dependency.
        user: Authenticated user (required).

    Raises:
        HTTP 404: If person not found.
        HTTP 401: If not authenticated.

    Examples:
        >>> DELETE /api/persons/P001
        >>> Response: 204 No Content
    """
    service.delete_person(person_id)


# ============================================================================
# Additional Endpoints
# ============================================================================


@router.get("/{person_id}/statistics", response_model=PersonStatistics)
async def get_person_statistics(
    person_id: str = Path(..., description="Person ID"),
    service: PersonService = Depends(get_person_service),
) -> PersonStatistics:
    """
    Get statistics for a person.

    Args:
        person_id: Person ID.
        service: PersonService dependency.

    Returns:
        Person statistics.

    Raises:
        HTTP 404: If person not found.

    Examples:
        >>> GET /api/persons/P001/statistics
        {
            "person_id": "P001",
            "full_name": "John Doe",
            "age": 34,
            "events_count": 5,
            "family_memberships": 2
        }
    """
    stats = service.get_person_statistics(person_id)
    # Map service field names to schema field names
    stats["family_memberships"] = stats.pop("families_count", 0)
    return PersonStatistics(**stats)


@router.get("/{person_id}/duplicates", response_model=List[PersonResponse])
async def find_potential_duplicates(
    person_id: str = Path(..., description="Person ID"),
    threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    service: PersonService = Depends(get_person_service),
) -> List[PersonResponse]:
    """
    Find potential duplicate persons.

    Args:
        person_id: Person ID to find duplicates for.
        threshold: Similarity threshold for fuzzy matching.
        service: PersonService dependency.

    Returns:
        List of potential duplicate persons.

    Raises:
        HTTP 404: If person not found.

    Examples:
        >>> GET /api/persons/P001/duplicates?threshold=0.8
        [
            {
                "id": "P123",
                "first_name": "Jon",
                "surname": "Doe",
                ...
            }
        ]
    """
    person = service.get_person(person_id)
    duplicates = service.find_potential_duplicates(
        person.first_name,
        person.surname,
        threshold=threshold,
    )
    return [person_to_response(p) for p in duplicates if p.id != person_id]
