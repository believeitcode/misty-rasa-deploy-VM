# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet
from rasa_sdk.events import EventType
import requests as rq
import sqlite3
import datetime


class ActionWeather(Action):

    def name(self) -> Text:
        return "action_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

            def weatherCity(city):
                API_KEY = "130043fb9b9b18097d439d12b5bb680f"
                base_url = "http://api.openweathermap.org/data/2.5/weather?"
    
     # GET http://api.openweathermap.org/data/2.5/weather?q=singapore&APPID=130043fb9b9b18097d439d12b5bb680f&units=metric&exclude=hourly,minutely,alerts
                Final_url = base_url + "appid=" + API_KEY + "&q=" + city + "&units=metric&exclude=hourly,minutely,alerts"
                weather_data = rq.get(Final_url).json()
                return weather_data
          # Make sure Skill match with UnqiueID .json of misty
          # POST <robot-ip-address>/api/skills/event with payload
            def mistyDisplayWeather(icon):
                url = "http://192.168.137.204/api/skills/event"
                body = {
                    "Skill": "16054f6d-d4b1-4577-b497-2d8092d178f0",
                    "EventName": "speakTheText",
                    "Payload": {
                        "icon": icon
                    }
                }
                rq.post(url, json=body).json()    

            # retrieve saved slot from rasa 
            city = tracker.get_slot('city')
            
        # list possible cities     
            possible_cities=["Singapore","Malaysia","Thailand"] 
            # read & parse the information and generate response
    
            if city in possible_cities:
                weatherAPIMain = weatherCity(city)['main']
                temperature = weatherAPIMain['temp']
                weatherAPIJson = weatherCity(city)
                condition = weatherAPIJson['weather'][0]["description"]
                wind = weatherAPIJson['wind']['speed']
                iconWeather = weatherAPIJson['weather'][0]["icon"]
                response = "The current temperature in {} is {} degres Celsius. It is {} and the wind speed is {} meter per second ".format(city,temperature,condition,wind)
                tempDisplay= str(temperature) + "℃"
                #mistyDisplayWeather(icon)
                dispatcher.utter_message(template="utter_weather", message=response, icon=iconWeather, display_txt=tempDisplay)
            else:    
                response = "Sorry, currently I am limited to information from Singapore, Malaysia and Thailand only."
                dispatcher.utter_message(template="utter_weather", message=response, icon="tears_face", display_txt="")
        
            #dispatcher.utter_message(template="utter_weather", message=response, icon=iconWeather)   
            slots_to_reset = ["city"]
            # reset slot
            return [SlotSet(slot, None) for slot in slots_to_reset]

class Action_Product_Search(Action):
    
    def name(self) -> Text:
        return "action_product_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # connect to DB
        connection = sqlite3.connect("retailDB.db")
        cursor = connection.cursor()

        # get slots and save as tuple
        colour_r = tracker.get_slot("colour")
        size_r = tracker.get_slot("size")
        shoe = [(colour_r), (size_r)]

        # place cursor on correct row based on search criteria
        cursor.execute("SELECT * FROM shoes_inventory WHERE colour=? AND size=?", shoe)
        
        # retrieve sqlite row
        data_row = cursor.fetchone()

        if data_row:
            # provide in stock message
            response = "You are lucky looks like we have size {} {} shoes in stock".format(size_r,colour_r)
            dispatcher.utter_message(template="utter_in_stock", message=response, icon="happy_face", display_txt="")
            #dispatcher.utter_message(template="utter_in_stock", size=size_r ,colour=colour_r) #TODO implement happy_face 
            connection.close()
            slots_to_reset = ["size", "colour"]
            # reset slot
            return [SlotSet(slot, None) for slot in slots_to_reset]
        else:
            # provide out of stock message
            response="Sorry, seems like we don't have those shoes, make sure you provide detail of color and size"
            dispatcher.utter_message(template="utter_no_stock", message=response, icon="sadness_face", display_txt="") #TODO implement sad_face
            connection.close()
            slots_to_reset = ["size", "colour"]
            # reset slot
            return [SlotSet(slot, None) for slot in slots_to_reset]

class ActionSubmitResults(Action):
    def name(self) -> Text:
        return "action_submit_results"
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        #get filled slot  
        customer_name_slot = tracker.get_slot("customer_name")
        colour_slot = tracker.get_slot("colour")
        size_slot = tracker.get_slot("size")

        # connect to DB
        connection = sqlite3.connect("retailDB.db")
        now = datetime.datetime.now()
        cursor = connection.cursor()

        shoe = [(colour_slot), (size_slot)]

        # place cursor on correct row based on search criteria
        cursor.execute("SELECT * FROM shoes_inventory WHERE colour=? AND size=?", shoe)
        connection.commit()
        # retrieve sqlite row
        data_row = cursor.fetchone()
        
        if data_row:
            order = [now.strftime("%Y-%m-%d"),now.strftime("%H:%M"),customer_name_slot,int(size_slot), colour_slot,"pending"]
            cursor.execute("INSERT INTO purchases VALUES (?,?,?,?,?,?)", order)
            response = "Thanks {} , your pre-order is sucessful for size {} and colour {} shoes. Please make payment at the counter".format(customer_name_slot,size_slot,colour_slot)
            dispatcher.utter_message(template="utter_purchase_success", message=response, icon="happy_face", display_txt="")
            #dispatcher.utter_message(template="utter_purchase_success", customer_name = customer_fs ,size=size_fs ,colour=colour_fs ) #TODO happy_face
            connection.commit()
            connection.close()
            slots_to_reset = ["customer_name","size", "colour"]
            return [SlotSet(slot, None) for slot in slots_to_reset]
        else:
            # provide out of stock
            #dispatcher.utter_message("order failed ,reason may due to the shoes you want are not available in stock , please try again")
            response = "pre-order failed ,reason may due to the shoes you want are not available in stock , please try again"
            dispatcher.utter_message(template="utter_purchase_fail", message=response, icon="sadness_face", display_txt="")
            connection.commit()
            connection.close()
            slots_to_reset = ["customer_name","size", "colour"]
            # reset slot
            return [SlotSet(slot, None) for slot in slots_to_reset]    
        

class ValidateFeedbackForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_feedback_form"

    async def validate_confirm_feedback(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value:
            return {"confirm_feedback": True}
        else:
            return {"feedback": "None", "confirm_feedback": False }

class ActionSubmitFeedback(Action):
    def name(self) -> Text:
        return "action_submit_feedback"

  
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

         # connect to DB
        connection = sqlite3.connect("retailDB.db")
        now = datetime.datetime.now()
        cursor = connection.cursor()


        confirm_feedback = tracker.get_slot('confirm_feedback')
        customer_feedback= tracker.get_slot('feedback')
        sentiment = tracker.get_slot('sentiment')

        if confirm_feedback is True:
            feedback = [now.strftime("%Y-%m-%d"),now.strftime("%H:%M"),"shoes",customer_feedback,sentiment]
            cursor.execute("INSERT INTO customer_feedback VALUES (?,?,?,?,?)", feedback)
            dispatcher.utter_message(response="utter_based_on_sentiment")
            connection.commit()
            connection.close()
            

        else:
            dispatcher.utter_message(template="utter_cancel_feedback")    

class Action_Find_Product_Price(Action):
    
    def name(self) -> Text:
        return "action_find_product_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # connect to DB
        connection = sqlite3.connect("retailDB.db")
        cursor = connection.cursor()

        # get slots and save as tuple
        product_s = tracker.get_slot("product")

        product = [(product_s)]


        # place cursor on correct row based on search criteria
        cursor.execute("SELECT * FROM product WHERE product_name=? ", product)
        
        # retrieve sqlite row
        data_row = cursor.fetchone()

        # retreive from cursor save as variable 
        
        if data_row:
            product_name_r = data_row[0]
            product_price_range_r = data_row[1]
            # provide in stock message
            response = "The {} start from {} dollar".format(product_name_r,product_price_range_r)
            priceDisplay = "$" + str(product_price_range_r)
            dispatcher.utter_message(template="utter_product_price", message=response, icon="star_face", display_txt=priceDisplay)
            #dispatcher.utter_message(template="utter_product_price", product_name=product_name_r ,product_price=product_price_range_r) #TODO Show price on Display ICON Extacy effect 
            connection.commit()
            connection.close()
            slots_to_reset = ["product"]
            return [SlotSet(slot, None) for slot in slots_to_reset]
            
        else:
            # provide out of stock message
            #dispatcher.utter_message(template="utter_no_stock") #TODO Sad face 
            response = "The following product {} , it can't be found in our store . You can make a feedback to tell us about it and we might bring it to our stocks".format(product_s)
            dispatcher.utter_message(template="utter_purchase_fail", message=response, icon="sadness_face", display_txt="")
            connection.commit()
            connection.close()
            slots_to_reset = ["product"]
            # reset slot
            return [SlotSet(slot, None) for slot in slots_to_reset]
      
