from sqlalchemy import ForeignKey, ARRAY, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure import Base


class ChemicalObject(Base):
    __tablename__ = 'chemicalobjects'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chemical_formula: Mapped[str] = mapped_column(nullable=False)
    source_check: Mapped[str] = mapped_column(nullable=False)
    molar_mass: Mapped[int] = mapped_column(nullable=False)

    target_operations: Mapped[list["ChemicalOperation"]] = relationship(
        back_populates="target_object",
        foreign_keys="[ChemicalOperation.target_id]",
        passive_deletes=True
    )

    composition_variants: Mapped[list["PercentChemicalElements"]] = relationship(
        back_populates="chemical_object",
        foreign_keys="[PercentChemicalElements.type_id]",
        passive_deletes=True
    )


class ChemicalOperation(Base):
    __tablename__ = 'chemicaloperations'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    target_id: Mapped[int] = mapped_column(ForeignKey('chemicalobjects.id', ondelete="CASCADE"))
    temperature: Mapped[int] = mapped_column(nullable=False)
    additional_conditions: Mapped[str] = mapped_column(nullable=True)

    target_object: Mapped["ChemicalObject"] = relationship(
        back_populates="target_operations"
    )


class PercentChemicalElements(Base):
    __tablename__ = 'percentchemicalelements'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(ForeignKey('chemicalobjects.id', ondelete="CASCADE"))
    main_percent: Mapped[float] = mapped_column(nullable=False)
    Fe_percent: Mapped[float] = mapped_column(nullable=False)
    Si_percent: Mapped[float] = mapped_column(nullable=False)
    K_percent: Mapped[float] = mapped_column(nullable=False)
    Ca_percent: Mapped[float] = mapped_column(nullable=False)
    Mg_percent: Mapped[float] = mapped_column(nullable=False)
    Na_percent: Mapped[float] = mapped_column(nullable=False)

    chemical_object: Mapped["ChemicalObject"] = relationship(
        back_populates="composition_variants"
    )
