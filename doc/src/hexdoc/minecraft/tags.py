from __future__ import annotations

from typing import Iterator, Self

from pydantic import Field

from hexdoc.utils import HexDocModel, LoaderContext, ResourceLocation
from hexdoc.utils.deserialize import decode_json_dict


class OptionalTagValue(HexDocModel, frozen=True):
    id: ResourceLocation
    required: bool


TagValue = ResourceLocation | OptionalTagValue


class Tag(HexDocModel):
    registry: str = Field(exclude=True)
    raw_values: set[TagValue] = Field(alias="values")
    replace: bool

    @classmethod
    def load(
        cls,
        registry: str,
        id: ResourceLocation,
        context: LoaderContext,
    ) -> Self:
        values = set[TagValue]()
        replace = False

        for _, _, tag in context.loader.load_resources(
            "data",
            f"tags/{registry}",
            id,
            decode=lambda s: Tag._convert(registry, s, context),
            export=cls._export,
        ):
            if tag.replace:
                values.clear()
            values.update(tag._load_values(context))

        return Tag(registry=registry, values=values, replace=replace)

    @classmethod
    def _convert(cls, registry: str, data: str, context: LoaderContext) -> Self:
        return cls.model_validate(
            decode_json_dict(data) | {"registry": registry},
            context=context,
        )

    @property
    def values(self) -> set[ResourceLocation]:
        return set(self.iter_values())

    def iter_values(self) -> Iterator[ResourceLocation]:
        for value in self.raw_values:
            match value:
                case ResourceLocation():
                    yield value
                case OptionalTagValue(id=id):
                    yield id

    def _export(self, current: Self | None):
        if self.replace or current is None:
            return self.model_dump_json()

        return self.model_copy(
            update={
                "raw_values": current.raw_values | self.raw_values,
            },
        ).model_dump_json()

    def _load_values(self, context: LoaderContext) -> Iterator[TagValue]:
        for value in self.raw_values:
            match value:
                case (
                    (ResourceLocation() as child_id) | OptionalTagValue(id=child_id)
                ) if child_id.is_tag:
                    try:
                        child = Tag.load(self.registry, child_id, context)
                        yield from child._load_values(context)
                    except FileNotFoundError:
                        yield value
                case _:
                    yield value