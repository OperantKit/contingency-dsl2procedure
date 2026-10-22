"""Reference / citation manager.

Citations are collected during compilation and rendered as a References
section at the end. Two sources:

1. **Auto-collected**: The compiler automatically adds citations when
   certain schedule features are encountered (e.g., Fleshler & Hoffman, 1962
   for variable schedules, Sidman, 1953 for avoidance).

2. **User-added**: Users can register additional Reference objects before
   or after compilation.

All references are rendered in APA 7th format by default; the Style
can override formatting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

CitationFormatter = Callable[["Reference"], str]


@dataclass(frozen=True)
class Reference:
    """A single bibliographic entry.

    Immutable so references can be safely shared across compilations.
    """

    key: str
    authors: str
    year: int | str
    title: str
    source: str
    volume: str = ""
    pages: str = ""
    doi: str = ""

    def to_apa7(self) -> str:
        """Render as APA 7th edition reference string."""
        parts = [f"{self.authors} ({self.year}). {self.title}."]
        if self.source:
            src = f"*{self.source}*"
            if self.volume:
                src += f", *{self.volume}*"
            if self.pages:
                src += f", {self.pages}"
            parts.append(f"{src}.")
        if self.doi:
            parts.append(self.doi)
        return " ".join(parts)

    def surnames(self) -> list[str]:
        """Author surnames from the reference-list form 'Last, F. M., & Last, F.'."""
        found = re.findall(r"([^\s,&][^,&]*?),\s*(?:[A-Z]\.\s*-?)+", self.authors)
        return [s.strip() for s in found] or [self.authors]

    def to_inline(self) -> str:
        """Render as APA narrative citation: 'Surname and Surname (Year)'."""
        names = self.surnames()
        if len(names) == 1:
            who = names[0]
        elif len(names) == 2:
            who = f"{names[0]} and {names[1]}"
        else:
            who = f"{names[0]} et al."
        return f"{who} ({self.year})"

    def to_parenthetical(self) -> str:
        """Render as parenthetical citation: '(Authors, Year)'."""
        return f"({self.authors}, {self.year})"

    def format(self, citation_format: str = "apa7") -> str:
        """Render using a registered citation formatter.

        Args:
            citation_format: Name of a formatter registered via
                ``register_citation_format``. Defaults to "apa7".

        Raises:
            KeyError: If the format name is not registered.
        """
        try:
            formatter = CITATION_FORMATTERS[citation_format]
        except KeyError as e:
            raise KeyError(
                f"unknown citation format {citation_format!r}; "
                f"registered: {sorted(CITATION_FORMATTERS)}"
            ) from e
        return formatter(self)


# ---------------------------------------------------------------------------
# Citation format registry
# ---------------------------------------------------------------------------

CITATION_FORMATTERS: dict[str, CitationFormatter] = {
    "apa7": lambda ref: ref.to_apa7(),
}


def register_citation_format(
    name: str, formatter: CitationFormatter, *, force: bool = False
) -> None:
    """Register a custom citation formatter.

    Args:
        name: Identifier used by ``Style.citation_format`` and
            ``Reference.format(name)``.
        formatter: Callable mapping a Reference to a rendered string.
        force: If False (default), raise ValueError on name collision.
            If True, overwrite silently.

    Raises:
        ValueError: If ``name`` is already registered and ``force`` is False.
    """
    if not force and name in CITATION_FORMATTERS:
        raise ValueError(
            f"citation format {name!r} is already registered; "
            f"pass force=True to overwrite"
        )
    CITATION_FORMATTERS[name] = formatter


def unregister_citation_format(name: str) -> None:
    """Remove a registered citation formatter.

    Raises:
        KeyError: If the format name is not registered.
    """
    del CITATION_FORMATTERS[name]


# ---------------------------------------------------------------------------
# Built-in references (auto-collected when relevant features are used)
# ---------------------------------------------------------------------------

FLESHLER_HOFFMAN_1962 = Reference(
    key="fleshler_hoffman_1962",
    authors="Fleshler, M., & Hoffman, H. S.",
    year=1962,
    title="A progression for generating variable-interval schedules",
    source="Journal of the Experimental Analysis of Behavior",
    volume="5",
    pages="529-530",
    doi="https://doi.org/10.1901/jeab.1962.5-529",
)

FERSTER_SKINNER_1957 = Reference(
    key="ferster_skinner_1957",
    authors="Ferster, C. B., & Skinner, B. F.",
    year=1957,
    title="Schedules of reinforcement",
    source="Appleton-Century-Crofts",
)

SIDMAN_1953 = Reference(
    key="sidman_1953",
    authors="Sidman, M.",
    year=1953,
    title="Avoidance conditioning with brief shock and no exteroceptive warning signal",
    source="Science",
    volume="118",
    pages="157-158",
    doi="https://doi.org/10.1126/science.118.3058.157",
)

HERRNSTEIN_1961 = Reference(
    key="herrnstein_1961",
    authors="Herrnstein, R. J.",
    year=1961,
    title="Relative and absolute strength of response as a function of frequency of reinforcement",
    source="Journal of the Experimental Analysis of Behavior",
    volume="4",
    pages="267-272",
    doi="https://doi.org/10.1901/jeab.1961.4-267",
)

HODOS_1961 = Reference(
    key="hodos_1961",
    authors="Hodos, W.",
    year=1961,
    title="Progressive ratio as a measure of reward strength",
    source="Science",
    volume="134",
    pages="943-944",
    doi="https://doi.org/10.1126/science.134.3483.943",
)

PAVLOV_1927 = Reference(
    key="pavlov_1927",
    authors="Pavlov, I. P.",
    year=1927,
    title="Conditioned reflexes: An investigation of the physiological activity of the cerebral cortex",
    source="Oxford University Press",
)

RESCORLA_1967 = Reference(
    key="rescorla_1967",
    authors="Rescorla, R. A.",
    year=1967,
    title="Pavlovian conditioning and its proper control procedures",
    source="Psychological Review",
    volume="74",
    pages="71-80",
    doi="https://doi.org/10.1037/h0024109",
)

SOLOMON_WYNNE_1953 = Reference(
    key="solomon_wynne_1953",
    authors="Solomon, R. L., & Wynne, L. C.",
    year=1953,
    title="Traumatic avoidance learning: Acquisition in normal dogs",
    source="Psychological Monographs",
    volume="67(4)",
    pages="Whole No. 354",
    doi="https://doi.org/10.1037/h0093649",
)

PLATT_1973 = Reference(
    key="platt_1973",
    authors="Platt, J. R.",
    year=1973,
    title="Percentile reinforcement: Paradigms for experimental analysis of response shaping",
    source="The Psychology of Learning and Motivation",
    volume="7",
    pages="271-296",
    doi="https://doi.org/10.1016/S0079-7421(08)60441-5",
)

PAGE_NEURINGER_1985 = Reference(
    key="page_neuringer_1985",
    authors="Page, S., & Neuringer, A.",
    year=1985,
    title="Variability is an operant",
    source="Journal of Experimental Psychology: Animal Behavior Processes",
    volume="11",
    pages="429-452",
    doi="https://doi.org/10.1037/0097-7403.11.3.429",
)

LEITENBERG_1965 = Reference(
    key="leitenberg_1965",
    authors="Leitenberg, H.",
    year=1965,
    title="Is time-out from positive reinforcement an aversive event? A review of the experimental evidence",
    source="Psychological Bulletin",
    volume="64",
    pages="428-441",
    doi="https://doi.org/10.1037/h0022657",
)

WEINER_1962 = Reference(
    key="weiner_1962",
    authors="Weiner, H.",
    year=1962,
    title="Some effects of response cost upon human operant behavior",
    source="Journal of the Experimental Analysis of Behavior",
    volume="5",
    pages="201-208",
    doi="https://doi.org/10.1901/jeab.1962.5-201",
)

KAZDIN_1972 = Reference(
    key="kazdin_1972",
    authors="Kazdin, A. E.",
    year=1972,
    title="Response cost: The removal of conditioned reinforcers for therapeutic change",
    source="Behavior Therapy",
    volume="3",
    pages="533-546",
    doi="https://doi.org/10.1016/S0005-7894(72)80002-7",
)

CATANIA_1966 = Reference(
    key="catania_1966",
    authors="Catania, A. C.",
    year=1966,
    title="Concurrent operants",
    source="Operant Behavior: Areas of Research and Application (W. K. Honig, Ed.)",
    pages="213-270",
)

TODOROV_1971 = Reference(
    key="todorov_1971",
    authors="Todorov, J. C.",
    year=1971,
    title="Concurrent performances: Effect of punishment contingent on the switching response",
    source="Journal of the Experimental Analysis of Behavior",
    volume="16",
    pages="51-62",
    doi="https://doi.org/10.1901/jeab.1971.16-51",
)

ESTES_SKINNER_1941 = Reference(
    key="estes_skinner_1941",
    authors="Estes, W. K., & Skinner, B. F.",
    year=1941,
    title="Some quantitative properties of anxiety",
    source="Journal of Experimental Psychology",
    volume="29",
    pages="390-400",
    doi="https://doi.org/10.1037/h0062283",
)

BROWN_JENKINS_1968 = Reference(
    key="brown_jenkins_1968",
    authors="Brown, P. L., & Jenkins, H. M.",
    year=1968,
    title="Auto-shaping of the pigeon's key-peck",
    source="Journal of the Experimental Analysis of Behavior",
    volume="11",
    pages="1-8",
    doi="https://doi.org/10.1901/jeab.1968.11-1",
)

WILLIAMS_WILLIAMS_1969 = Reference(
    key="williams_williams_1969",
    authors="Williams, D. R., & Williams, H.",
    year=1969,
    title="Auto-maintenance in the pigeon: Sustained pecking despite contingent non-reinforcement",
    source="Journal of the Experimental Analysis of Behavior",
    volume="12",
    pages="511-520",
    doi="https://doi.org/10.1901/jeab.1969.12-511",
)

BOUTON_2004 = Reference(
    key="bouton_2004",
    authors="Bouton, M. E.",
    year=2004,
    title="Context and behavioral processes in extinction",
    source="Learning & Memory",
    volume="11",
    pages="485-494",
    doi="https://doi.org/10.1101/lm.78804",
)

SKINNER_1953 = Reference(
    key="skinner_1953",
    authors="Skinner, B. F.",
    year=1953,
    title="Science and human behavior",
    source="Macmillan",
)

GALBICKA_1994 = Reference(
    key="galbicka_1994",
    authors="Galbicka, G.",
    year=1994,
    title="Shaping in the 21st century: Moving percentile schedules into applied settings",
    source="Journal of Applied Behavior Analysis",
    volume="27",
    pages="739-760",
    doi="https://doi.org/10.1901/jaba.1994.27-739",
)

ZEILER_1968 = Reference(
    key="zeiler_1968",
    authors="Zeiler, M. D.",
    year=1968,
    title="Fixed and variable schedules of response-independent reinforcement",
    source="Journal of the Experimental Analysis of Behavior",
    volume="11",
    pages="405-414",
    doi="https://doi.org/10.1901/jeab.1968.11-405",
)

MILLENSON_1963 = Reference(
    key="millenson_1963",
    authors="Millenson, J. R.",
    year=1963,
    title="Random interval schedules of reinforcement",
    source="Journal of the Experimental Analysis of Behavior",
    volume="6",
    pages="437-443",
    doi="https://doi.org/10.1901/jeab.1963.6-437",
)

MCSWEENEY_NORMAN_1979 = Reference(
    key="mcsweeney_norman_1979",
    authors="McSweeney, F. K., & Norman, W. D.",
    year=1979,
    title="Defining behavioral contrast for multiple schedules",
    source="Journal of the Experimental Analysis of Behavior",
    volume="32",
    pages="457-461",
    doi="https://doi.org/10.1901/jeab.1979.32-457",
)

MALAGODI_1973 = Reference(
    key="malagodi_1973",
    authors="Malagodi, E. F., DeWeese, J., & Johnston, J. M.",
    year=1973,
    title="Second-order schedules: A comparison of chained, brief-stimulus, and tandem procedures",
    source="Journal of the Experimental Analysis of Behavior",
    volume="20",
    pages="447-461",
    doi="https://doi.org/10.1901/jeab.1973.20-447",
)

RICHARDS_1993 = Reference(
    key="richards_1993",
    authors="Richards, J. B., Sabol, K. E., & Seiden, L. S.",
    year=1993,
    title="DRL interresponse-time distributions: Quantification by peak deviation analysis",
    source="Journal of the Experimental Analysis of Behavior",
    volume="60",
    pages="361-385",
    doi="https://doi.org/10.1901/jeab.1993.60-361",
)

REED_2003 = Reference(
    key="reed_2003",
    authors="Reed, P.",
    year=2003,
    title="The differentiation of response rates by humans: The role of differential-reinforcement-of-high-rate (DRH) schedules",
    source="Animal Learning & Behavior",
    volume="31",
    pages="227-238",
    doi="https://doi.org/10.3758/bf03195983",
)

REY_2019 = Reference(
    key="rey_2019",
    authors="Rey, C. N., Thrailkill, E. A., Goldberg, K. L., & Bouton, M. E.",
    year=2019,
    title="Relapse of operant behavior after response elimination with an extinction or an omission contingency",
    source="Journal of the Experimental Analysis of Behavior",
    volume="113",
    pages="1-17",
    doi="https://doi.org/10.1002/jeab.568",
)

HUNTER_DAVISON_1985 = Reference(
    key="hunter_davison_1985",
    authors="Hunter, I., & Davison, M.",
    year=1985,
    title="Determination of a behavioral transfer function: White-noise analysis of session-to-session response-ratio dynamics on concurrent VI VI schedules",
    source="Animal Learning & Behavior",
    volume="13",
    pages="293-299",
    doi="https://doi.org/10.3758/BF03197983",
)

# Lookup table: key -> Reference
BUILTIN_REFERENCES: dict[str, Reference] = {
    r.key: r
    for r in [
        FLESHLER_HOFFMAN_1962,
        FERSTER_SKINNER_1957,
        SIDMAN_1953,
        HERRNSTEIN_1961,
        HODOS_1961,
        PAVLOV_1927,
        RESCORLA_1967,
        SOLOMON_WYNNE_1953,
        PLATT_1973,
        PAGE_NEURINGER_1985,
        LEITENBERG_1965,
        WEINER_1962,
        KAZDIN_1972,
        CATANIA_1966,
        TODOROV_1971,
        ESTES_SKINNER_1941,
        BROWN_JENKINS_1968,
        WILLIAMS_WILLIAMS_1969,
        BOUTON_2004,
        SKINNER_1953,
        GALBICKA_1994,
        ZEILER_1968,
        MILLENSON_1963,
        MCSWEENEY_NORMAN_1979,
        MALAGODI_1973,
        RICHARDS_1993,
        REED_2003,
        REY_2019,
        HUNTER_DAVISON_1985,
    ]
}


@dataclass
class ReferenceCollector:
    """Accumulates references during a single compilation pass.

    Usage:
        collector = ReferenceCollector()
        collector.cite("fleshler_hoffman_1962")  # auto-collected
        collector.add(custom_ref)                 # user-added
        refs = collector.sorted_references()
    """

    _refs: dict[str, Reference] = field(default_factory=dict)

    def cite(self, key: str) -> Reference:
        """Record a built-in reference by key. Returns the Reference for inline use.

        Raises:
            KeyError: If the key is not in BUILTIN_REFERENCES.
        """
        ref = BUILTIN_REFERENCES[key]
        self._refs[key] = ref
        return ref

    def cite_if_known(self, key: str) -> Reference | None:
        """Record a built-in reference if it exists; return None otherwise."""
        ref = BUILTIN_REFERENCES.get(key)
        if ref is not None:
            self._refs[key] = ref
        return ref

    def add(self, ref: Reference) -> None:
        """Add a user-provided reference."""
        self._refs[ref.key] = ref

    def sorted_references(self) -> list[Reference]:
        """Return all collected references sorted alphabetically by APA convention."""
        return sorted(self._refs.values(), key=lambda r: r.authors.lower())

    def render_list(self, *, format: str = "apa7") -> str:
        """Render the full reference list as a string."""
        refs = self.sorted_references()
        if not refs:
            return ""
        return "\n".join(r.format(format) for r in refs)

    def __len__(self) -> int:
        return len(self._refs)

    def __contains__(self, key: str) -> bool:
        return key in self._refs
