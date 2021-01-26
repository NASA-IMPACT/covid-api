"""Exceptions for the endpoints classes"""


class NonRasterDataset(Exception):
    """Thrown if timelapse requested for a non-raster dataset"""

    pass


class UnableToExtractS3Url(Exception):
    """Thrown if code is not ale to extract the S3 URL of the dataset """

    pass


class InvalidDateFormat(Exception):
    """Thrown if the timelapse request query contains a date that is not correctly
     formatted for the given dataset """

    pass


class MissingSpotlightId(Exception):
    """Thrown if the timelapse request query is for a spotlight specific dataset,
    but no spotlightId was supplied in the query """

    pass
