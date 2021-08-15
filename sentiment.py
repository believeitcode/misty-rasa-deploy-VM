from rasa.nlu.components import Component
from rasa.nlu import utils
from rasa.nlu.model import Metadata

import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os

class SentimentAnalyzer(Component):
    """A pre-trained sentiment component"""

    name = "sentiment"
    provides = ["entities"]
    requires = []
    defaults = {}
    language_list = ["en"]

    @classmethod
    def required_packages(cls):
        return ["nltk"]

    def __init__(self, component_config=None):
        super(SentimentAnalyzer, self).__init__(component_config)

    def train(self, training_data, cfg, **kwargs):
        """Not needed, because the the model is pretrained"""
        pass



    def convert_to_rasa(self, value, confidence):
        """Convert model output into the Rasa NLU compatible output format."""
        
        entity = {"value": value,
                  "confidence": confidence,
                  "entity": "sentiment",
                  "extractor": "sentiment_extractor"}

        return entity


    def process(self, message, **kwargs):
        """Retrieve the text message, pass it to the classifier
            and append the prediction results to the message class."""

        sid = SentimentIntensityAnalyzer()

        #Take Note In rasa 2.X text is in dictionary attribute 
        data = ""
        try:
            data = message.data['text']
        except KeyError:
            pass    
        
        
        res = sid.polarity_scores(data)
        key, value = max(res.items(), key=lambda x: x[1])

        entity = self.convert_to_rasa(key, value)

        message.set("entities", [entity], add_to_output=True)


## Ref: https://blog.rasa.com/enhancing-rasa-nlu-with-custom-components/ 
## Fix :https://forum.rasa.com/t/message-object-does-not-recognize-text-attribute-in-custom-component-for-rasa-2-0/36313/10