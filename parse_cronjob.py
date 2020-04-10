from mongodb_utils import result_write_callback
from instagram_utils import parse_by_tag
import os
import datetime


# some variables from env
max_iterations_with_no_new_posts = int(os.getenv('MAX_ITERATIONS_WITH_NO_NEW_POSTS', '30'))
days_to_dig = int(os.getenv('DAYS_TO_DIG', '3'))


queries = ["covid", "covıd", "covid19", "covıd19", "covi̇d19", "covi̇d_19", "covid2020", "covidmemes", "coronavid19",
           "covod19", "coronavairus", "cvid19", "covidiot", "novelcorona", "covidindia", "pandemic2020",
           "covidkindness", "pandemicpreparedness", "covidnews", "2019ncov", "sarscov2", "sars_cov_2", "coronaeurope",
           "coronausa", "coronaworld", "coronachina", "coronacapital", "coronaupdate", "coronaextra", "instacorona",
           "coronawuhan", "coronaitaly", "coronavırusnews", "covid20", "cốvịdịch", "coronacases", "wuhanchina",
           "pandemic", "coronaprotection", "coronacure", "coronafight", "coronasymptoms", "sarcov2", "covidgermany",
           "ncov", "ncov2019", "ncov2020", "коронавирус", "2019ncov"]


if __name__ == '__main__':
    new_border_time = datetime.datetime.now() - datetime.timedelta(days=days_to_dig)
    new_border_time = int(new_border_time.timestamp())

    for i, _TAG in enumerate(queries):
        print(i+1, 'start parsing for tag', _TAG)
        parse_by_tag(
            _TAG,
            write_callback=result_write_callback,
            new_border_time=new_border_time,
            max_iterations_with_no_new_posts=max_iterations_with_no_new_posts
        )
        print(i+1, 'end parsing for tag', _TAG)
