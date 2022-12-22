# ArticleTopicSentimentAnalysis
A basic sentiment analysis tool that retrieves articles from the GDELT 2.0 database and performs sentiment analysis using VADER.

**Articles are retrieved using a near word search which finds articles containing words that occur within n words of each other. A list of key words and near words are input and a call is made for every key word and near word pair.**

**Default topic is semiconductor supply chain**

**Returned paramaters:**

Title - Title of the article

Summary - Summary of the text within the article. Expected to be 3 sentences long if article text is 100-1500 words in length, 5 sentences long if 1500-5000 words in length, or 7 sentences long if >5000 words in length

Score - Sentiment score of the article summary. Attempts to identify the emotional tone behind a body of text, negative associating to a negative tone and positive associating to a positive tone, ranges from -1 to 1.

Subjectivity - Subjectivity score of the article summary. Attempts to identify the bias or influence of personal feelings in a body of text. Ranges from 0 to 1, 0 being completely unbiased/factual and 1 being highly biased or highly influenced by feeling.

URL - URL of article

Date - Date that the article was published

Domain - Domain that the article was retrieved from

Language - Language of the article

Source Country - Country that the article was published from

Country1/Country2/Country3 - Three most mentioned countries within the text, 1 being the most mentioned country, 2 being the 2nd most mentioned country, and 3 being the 3rd most mentioned country.

**Available filter parameters can be found here: https://github.com/alex9smith/gdelt-doc-api**
