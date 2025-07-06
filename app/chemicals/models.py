from sqlalchemy import ForeignKey, ARRAY, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure import Base


class ChemicalObject(Base):
    __tablename__ = 'chemicalobjects'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chemical_formula: Mapped[str] = mapped_column(nullable=False)

    target_operations: Mapped[list["ChemicalOperation"]] = relationship(
        back_populates="target_object",
        foreign_keys="[ChemicalOperation.target_id]"
    )


class ChemicalOperation(Base):
    __tablename__ = 'chemicaloperations'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    target_id: Mapped[int] = mapped_column(ForeignKey('chemicalobjects.id'))
    temperature: Mapped[int] = mapped_column(nullable=False)
    additional_conditions: Mapped[str] = mapped_column(nullable=True)

    target_object: Mapped["ChemicalObject"] = relationship(
        back_populates="target_operations"
    )
