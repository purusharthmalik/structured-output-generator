from typing import Optional
from pydantic import BaseModel, Field

class Dining(BaseModel):
    """Variables for the dining category"""
    date: str = Field(description="Date of the dining experience")
    time: str = Field(description="Time of the dining experience")
    cuisine: str = Field(description="Cuisine type")
    location: str = Field(description="Location of the restaurant")
    party_size: int = Field(description="Number of people in the dining party")
    price_range: Optional[str] = Field(description="Price range of the restaurant, e.g., cheap, moderate, expensive")
    dietary_restrictions: Optional[str] = Field(description="Dietary restrictions, e.g., vegetarian, vegan, gluten-free")
    other_requests: Optional[str] = Field("Any other requests or preferences")

class Travel(BaseModel):
    """Variables for the travel category"""
    destination: str = Field(description="Travel destination")
    departure_date: str = Field(description="Departure date")
    return_date: str = Field(description="Return date")
    budget: Optional[str] = Field(description="Budget for the trip")
    activities: Optional[str] = Field(description="Preferred activities, e.g., sightseeing, adventure, relaxation")
    other_requests: Optional[str] = Field("Any other requests or preferences")

class Gifting(BaseModel):
    """Variables for the gifting category"""
    occasion: str = Field(description="Occasion for the gift")
    recipient_age: str = Field(description="Age of the recipient")
    budget: Optional[str] = Field(description="Budget for the gift")
    interests: Optional[str] = Field(description="Interests or hobbies of the recipient")
    other_requests: Optional[str] = Field("Any other requests or preferences")

class CabBooking(BaseModel):
    """Variables for the cab booking category"""
    pickup_location: str = Field(description="Pickup location")
    dropoff_location: str = Field(description="Dropoff location")
    pickup_time: str = Field(description="Pickup time")
    dropoff_time: Optional[str] = Field(description="Dropoff time")
    vehicle_type: Optional[str] = Field(description="Type of vehicle, e.g., sedan, SUV, van")
    other_requests: Optional[str] = Field("Any other requests or preferences")

class Other(BaseModel):
    """Variables for the other categories"""
    description: str = Field(description="Description of the request")
    other_requests: Optional[str] = Field("Any other requests or preferences")

class Classification(BaseModel):
    """Class for initial classification of the request"""
    category: str = Field(description="Category of the request")
    confidence: float = Field(description="Confidence level of the classification")