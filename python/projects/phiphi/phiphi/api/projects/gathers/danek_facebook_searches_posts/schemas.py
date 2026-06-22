"""Danek Facebook searches posts gather schema."""

import enum
from typing import Annotated, Optional

import pydantic

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers import utils
from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ProxyCodes(str, enum.Enum):
    """Enum for Danek API proxy codes."""

    US = "us"
    VN = "vn"
    BR = "br"
    GB = "gb"
    DE = "de"
    AR = "ar"
    CA = "ca"
    ID = "id"
    IT = "it"
    EC = "ec"
    ES = "es"
    PH = "ph"
    RU = "ru"
    FR = "fr"
    EG = "eg"
    MX = "mx"
    PL = "pl"
    RO = "ro"
    IQ = "iq"
    ZA = "za"
    IN_ = "in"  # 'in' is a reserved word in Python.
    AU = "au"
    JP = "jp"
    PE = "pe"
    UA = "ua"
    CL = "cl"
    HK = "hk"
    TR = "tr"
    NL = "nl"
    MY = "my"
    CO = "co"
    SE = "se"
    TT = "tt"
    PT = "pt"
    SA = "sa"
    TH = "th"
    SG = "sg"
    VE = "ve"
    KR = "kr"
    RS = "rs"
    CN = "cn"
    HU = "hu"
    KE = "ke"
    JM = "jm"
    CH = "ch"
    FI = "fi"
    IE = "ie"
    BG = "bg"
    DZ = "dz"
    DO = "do"
    PK = "pk"
    BD = "bd"
    BO = "bo"
    TW = "tw"
    AT = "at"
    GR = "gr"
    UZ = "uz"
    LV = "lv"
    IL = "il"
    BB = "bb"
    KZ = "kz"
    LK = "lk"
    BE = "be"
    DK = "dk"
    AZ = "az"
    CZ = "cz"
    NZ = "nz"
    PR = "pr"
    PY = "py"
    GT = "gt"
    HN = "hn"
    JO = "jo"
    MA = "ma"
    IR = "ir"
    PA = "pa"
    AE = "ae"
    NO = "no"
    SK = "sk"
    AL = "al"
    BS = "bs"
    AM = "am"
    SV = "sv"
    EE = "ee"
    UY = "uy"
    CR = "cr"
    LB = "lb"
    HR = "hr"
    LT = "lt"
    MD = "md"
    NP = "np"
    LY = "ly"
    BA = "ba"
    KW = "kw"
    TN = "tn"
    MK = "mk"
    GE = "ge"
    OM = "om"
    IS_ = "is"  # 'is' is a reserved word.
    SY = "sy"
    BW = "bw"
    CY = "cy"
    MM = "mm"
    BY = "by"
    CI = "ci"
    KH = "kh"
    QA = "qa"
    NI = "ni"
    SN = "sn"
    CW = "cw"
    SI = "si"
    GY = "gy"
    BH = "bh"
    ET = "et"
    MU = "mu"
    KG = "kg"
    PS = "ps"
    LC = "lc"
    BZ = "bz"
    XK = "xk"
    MT = "mt"
    VI = "vi"
    GD = "gd"
    GH = "gh"
    NG = "ng"
    BM = "bm"
    KY = "ky"
    AG = "ag"
    ML = "ml"
    CG = "cg"
    SD = "sd"
    VC = "vc"
    TZ = "tz"
    AW = "aw"
    ME = "me"
    YE = "ye"
    RE = "re"
    BN = "bn"
    GA = "ga"
    AO = "ao"
    VG = "vg"
    LA = "la"
    CD = "cd"
    BF = "bf"
    TJ = "tj"
    UG = "ug"
    TG = "tg"
    LU = "lu"
    FJ = "fj"
    SR = "sr"
    IM = "im"
    MN = "mn"
    MO = "mo"
    GP = "gp"
    SL = "sl"
    JE = "je"
    KN = "kn"
    MQ = "mq"
    MV = "mv"
    DM = "dm"
    GU = "gu"
    CV = "cv"
    RW = "rw"
    MZ = "mz"
    GG = "gg"
    MW = "mw"
    ZM = "zm"
    ZW = "zw"
    CM = "cm"
    GF = "gf"
    CU = "cu"
    TC = "tc"
    AD = "ad"
    SO = "so"
    BJ = "bj"
    SX = "sx"
    GM = "gm"
    BT = "bt"
    NA = "na"
    MR = "mr"
    SC = "sc"
    AF = "af"
    BQ = "bq"
    GI = "gi"
    SZ = "sz"
    MF = "mf"
    NC = "nc"
    HT = "ht"
    PF = "pf"
    TM = "tm"
    ST = "st"
    AI = "ai"
    MG = "mg"
    MS = "ms"
    GN = "gn"
    SM = "sm"
    SS = "ss"
    GQ = "gq"
    LI = "li"
    PG = "pg"
    MC = "mc"
    TL = "tl"
    WF = "wf"
    BI = "bi"
    GL = "gl"
    NE = "ne"
    LS = "ls"
    CK = "ck"
    KM = "km"
    DJ = "dj"
    AS_ = "as"  # 'as' is a reserved word.
    TD = "td"


def validate_date_range(
    posts_created_after: Optional[str], posts_created_before: Optional[str]
) -> None:
    """Validate that range between posts_created_after and posts_created_before."""
    if posts_created_after is None or posts_created_before is None:
        return

    before = utils.parse_datetime_string(posts_created_before)
    after = utils.parse_datetime_string(posts_created_after)

    if before <= after:
        raise ValueError("posts_created_before must be after posts_created_after")


ValidatedDate = Annotated[
    Optional[str], pydantic.AfterValidator(utils.validate_and_normalise_datetime)
]
VALIDATED_DATE_DESCRIPTION = (
    "A Datetime in any format support by libary dateutil."
    " Will be converted to ISO 8601 and UTC timezone."
    "If only date is given it will be converted to 00:00:00 UTC."
)

POSTS_CREATED_AFTER_DESCRIPTION = (
    f"Fetch posts created after this date. {VALIDATED_DATE_DESCRIPTION}"
)
POSTS_CREATED_BEFORE_DESCRIPTION = (
    f"Fetch posts created before this date. {VALIDATED_DATE_DESCRIPTION}"
)


class DanekFacebookSearchesPostsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Danek Facebook Scraper for searches."""

    stop_scraping_per_search_after_count: int = pydantic.Field(
        description="Stop scraping after post count, per search."
    )
    search_list: list[str] = pydantic.Field(
        description=("List of searches to scrape Facebook Posts for."),
    )
    proxy_country_to_gather_from: Optional[ProxyCodes] = pydantic.Field(
        default=None,
        description=("Country to use for the proxy to gather from."),
    )
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_AFTER_DESCRIPTION,
    )
    posts_created_before: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_BEFORE_DESCRIPTION,
    )
    recent_posts: bool = pydantic.Field(
        default=True,
        description=(
            "Whether to check the recent posts element for posts search, "
            "see https://www.facebook.com/search/posts?q=hello "
            "for the UI input and an example. "
            "Defaults to True."
        ),
    )

    @pydantic.model_validator(mode="after")
    def validate_dates_order(self) -> "DanekFacebookSearchesPostsGatherBase":
        """Validate that posts_created_before is after posts_created_after."""
        validate_date_range(self.posts_created_after, self.posts_created_before)
        return self


class DanekFacebookSearchesPostsGatherResponse(
    gather_schemas.GatherChildResponseBase, DanekFacebookSearchesPostsGatherBase
):
    """Danek Facebook searches posts gather schema."""

    # Both the property and computed_field decorators are used other wise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Calculate the resource estimate for the job run."""
        max_gather_result_count: int = (
            len(self.search_list) * self.stop_scraping_per_search_after_count
        )
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_danek_costs_per_100k(
                gather_schemas.ChildTypeName.danek_facebook_searches_posts
            ),
        )


class DanekFacebookSearchesPostsGatherCreate(
    gather_schemas.GatherCreate, DanekFacebookSearchesPostsGatherBase
):
    """Danek Gather create schema.

    Properties to receive via API on creation.
    """


class DanekFacebookSearchesPostsGatherUpdate(gather_schemas.GatherUpdate):
    """Danek Gather update schema.

    Properties to receive via API on update.
    """

    stop_scraping_per_search_after_count: Optional[int] = pydantic.Field(
        description="Stop scraping after post count, per search."
    )
    search_list: Optional[list[str]] = pydantic.Field(
        description=("List of searches to scrape Facebook Posts for."),
    )
    proxy_country_to_gather_from: Optional[str] = pydantic.Field(
        default=None,
        description=("Country to use for the proxy to gather from."),
    )
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_AFTER_DESCRIPTION,
    )
    posts_created_before: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_BEFORE_DESCRIPTION,
    )
    recent_posts: Optional[bool] = pydantic.Field(
        description=(
            "Whether to check the recent posts element for posts search, "
            "see https://www.facebook.com/search/posts?q=hello "
            "for the UI input and an example. "
            "Defaults to True."
        ),
    )

    @pydantic.model_validator(mode="after")
    def validate_dates_order(self) -> "DanekFacebookSearchesPostsGatherUpdate":
        """Validate that posts_created_before is after posts_created_after."""
        validate_date_range(self.posts_created_after, self.posts_created_before)
        return self
