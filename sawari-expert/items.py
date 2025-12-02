# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SawariexpertItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ModelInfoItem(scrapy.Item):
    """Item for model information"""
    brandName = scrapy.Field()
    modelName = scrapy.Field()
    modelDescription = scrapy.Field()
    modelTagline = scrapy.Field()
    modelIsHiglighted = scrapy.Field()
    bodyType = scrapy.Field()


class RatingInfoItem(scrapy.Item):
    """Item for rating information"""
    modelName = scrapy.Field()
    ratingCategoryName = scrapy.Field()
    rating = scrapy.Field()
