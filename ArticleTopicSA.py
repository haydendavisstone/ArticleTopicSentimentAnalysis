import json
import os
import re

import dateutil
from gdeltdoc import GdeltDoc, Filters, near, repeat
import locationtagger
from newspaper import Article
from newspaper import Config
import pandas
from sumy.nlp.stemmers import Stemmer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.utils import get_stop_words
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

N_TOP_COUNTRIES = 3

NEAR_WORDS_SOURCE = os.path.join("inputs", "nearwords.json")


#These variables change the input parameters in the filter object
NUMBER_OF_RECORDS = 10 #number of articles retrieved per call
START_DATE = "2022-03-31" #change start and end date values to retrieve articles within a date range
END_DATE = "2022-01-02"  #to use date range functionality, the start date and end date parameters in the filter objects must be uncommented and the timespan parameter must be commented
COUNTRIES = ["US", "UK", "CA"] #countries that articles are retrieved from
WORD_PROXIMITY = 10 #nearword term proximity
LANGUAGE = "english" #language of parsed text

SIA = SentimentIntensityAnalyzer()

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
cfg = Config()
cfg.browser_user_agent = user_agent

pandas.set_option('display.max_colwidth', None)
pandas.set_option("display.max_columns", 15)
pandas.set_option("display.max_rows", 10)

df_columns = [
'title',
'summary',
'score',
'subjectivity',
'url',
'date',
'domain',
'language',
'sourcecountry',
'country1',
'country2',
'country3'
]

def sentiment_scores(sentence):
    sentiment_dict = SIA.polarity_scores(sentence)
    score = sentiment_dict['compound']
    return score

def getSubjectivity(text):
   texttemp = TextBlob(text)
   subj = texttemp.sentiment.subjectivity
   return subj

def main():
    gd = GdeltDoc()

    with open(NEAR_WORDS_SOURCE) as f:
        nearwords = json.load(f)

    articledf = pandas.DataFrame(columns = df_columns)

    #stores the variables in the given search terms file into the SEARCH_TERM_SOURCE variable
    #change the second input parameter to another file name to change the topic, file names can be found in the input folder
    SEARCH_TERM_SOURCE = os.path.join("inputs", 'keywords.json')

    with open(SEARCH_TERM_SOURCE) as f:
        keywords = json.load(f)

    for keyword in keywords:
        for nearword in nearwords:
            f = Filters(
                # keyword = "",
                num_records = NUMBER_OF_RECORDS,
                timespan = "5d", #uncomment for timespan functionality, comment for date range functionality
                # start_date = START_DATE, #uncomment for date range functionality, comment for timespan functionality
                # end_date = END_DATE, 
                country = COUNTRIES,
                near = near(WORD_PROXIMITY, keyword, nearword),
                # repeat = repeat(2, "") #use to retrieve articles containing a term that repeats n number of times
            )

            articles = gd.article_search(f)

            if articles.empty:
                continue

            articles = articles.drop(columns = ['url_mobile', 'socialimage'])
            articles = articles[articles['language'] == 'English']
            articles = articles.rename(columns = {'seendate':'date'})
            articles = articles.reindex(columns = df_columns)

            for dfindex, row in articles.iterrows():
                url = row['url']
                article = Article(url,config=cfg)
                try:
                    article.download()
                    article.parse()
                    article.nlp()
                except:
                    articles = articles.drop(dfindex)
                    continue

                datetemp = row['date']
                datetemp = datetemp.split('T', 1)[0]
                dt = dateutil.parser.parse(datetemp)
                dt = dt.strftime('%Y-%m-%d')

                article_text = article.text
                article_text = article_text.replace("\n", "")
                # Find sentences with no spaces after the period and add those
                # spaces.
                article_text = (
                    re.sub(r'\.(?! )', '. ', re.sub(r' +', ' ', article_text))
                )

                if not article_text:
                    articles = articles.drop(dfindex)
                    continue

                parser = PlaintextParser.from_string(article_text, Tokenizer(LANGUAGE))
                stemmer = Stemmer(LANGUAGE)
                summarizer = Summarizer(stemmer)
                summarizer.stop_words = get_stop_words(LANGUAGE)

                totalscore = 0
                totalsubj = 0
                sumtext = ''

                if len(article_text) <= 100:
                    articles = articles.drop(dfindex)
                    continue
                elif len(article_text) > 100 & len(article_text) <= 1500:
                    SENTENCES_COUNT = 3
                elif len(article_text) > 1500 & len(article_text) < 5000:
                    SENTENCES_COUNT = 5
                else:
                    SENTENCES_COUNT = 7

                for sentence in summarizer(parser.document, SENTENCES_COUNT):
                    totalscore += sentiment_scores(str(sentence))
                    totalsubj +=  getSubjectivity(str(sentence))
                    sumtext += (' ' + str(sentence))

                scoreavg = totalscore / SENTENCES_COUNT
                subj = totalsubj / SENTENCES_COUNT

                place_entity = locationtagger.find_locations(text = article_text)

                # List of tuples (key, value).
                # Keys are countries, values are # of times a country is mentioned in
                # a specific article.
                country = place_entity.country_mentions
                country_mentions = {}

                for country_name, n_mentions in country:
                    if country_name in country_mentions:
                        country_mentions[country_name] += n_mentions
                    else:
                        country_mentions[country_name] = n_mentions

                country = [
                    (country_name, n_mentions)
                    for country_name, n_mentions in country_mentions.items()
                ]

                country.sort(key = lambda tuple_: tuple_[1])

                for i_, country_mention in enumerate(country[:N_TOP_COUNTRIES]):
                    country_name = country_mention[0]
                    articles.loc[dfindex, f"country{i_ + 1}"] = country_name

                articles.loc[dfindex,'summary'] = sumtext
                articles.loc[dfindex,'date'] = dt
                articles.loc[dfindex,'score'] = scoreavg
                articles.loc[dfindex,'subjectivity'] = subj

            if articles.empty == False:
                articledf = pandas.concat([articledf, articles], axis = 0)

    articledf = articledf.drop_duplicates(subset=['title'])

    articledf.to_csv('output.csv', encoding='utf-8-sig', index=False)
    print('file saved')

if __name__ == "__main__" :
    main()

