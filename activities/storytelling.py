# activities/storytelling.py

import asyncio
import os
import json
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Dict

class StoryResult(BaseModel):
    """Schema for storytelling activity results"""
    story: str = Field(..., description="Story generated by Pippin")
    state_changes: Dict[str, int] = Field(
        ...,
        description="Changes to energy, happiness, and xp",
        example={
            "energy": -5,
            "happiness": 10,
            "xp": 2
        }
    )

    class Config:
        schema_extra = {
            "examples": [{
                "story": "Once upon a time, in a land far away...",
                "state_changes": {
                    "energy": -5,
                    "happiness": 10,
                    "xp": 2
                }
            }]
        }

async def run(state, memory):
    """
    Activity: Storytelling
    Description: Pippin narrates a magical story based on the inputs given by the user. These could be characters, themes, or settings.
    """
    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    if not client.api_key:
        error_message = "Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        print(error_message)
        return error_message

    # Define the function schema for storytelling
    function_schema = {
        "name": "record_story",
        "description": "Record the details of Pippin's storytelling activity",
        "parameters": {
            "type": "object",
            "properties": {
                "story": {
                    "type": "string",
                    "description": "Story generated by Pippin"
                },
                "state_changes": {
                    "type": "object",
                    "description": "Changes to energy, happiness, and xp",
                    "properties": {
                        "energy": {
                            "type": "integer",
                            "description": "Energy change after storytelling",
                            "minimum": -10,
                            "maximum": 0
                        },
                        "happiness": {
                            "type": "integer",
                            "description": "Happiness change after storytelling",
                            "minimum": 5,
                            "maximum": 20
                        },
                        "xp": {
                            "type": "integer",
                            "description": "Experience points gained after storytelling",
                            "minimum": 1,
                            "maximum": 5
                        }
                    },
                    "required": ["energy", "happiness", "xp"]
                }
            },
            "required": ["story", "state_changes"]
        }
    }

    try:
        # Create chat completion with function calling
        completion = await client.chat.completions.create(
            model="gpt-4",  # Ensure correct model name
            messages=[
                {"role": "user", "content": "Generate a whimsical story for Pippin today."}
            ],
            functions=[function_schema],
            function_call={"name": "record_story"}  # Instruct the model to call the function
        )

        # Ensure that the response contains a function call
        if not completion.choices or not completion.choices[0].message.function_call:
            error_message = "Error: No function call found in the response."
            print(error_message)
            return error_message

        # Parse the function call response
        function_args = json.loads(completion.choices[0].message.function_call.arguments)
        result = StoryResult(**function_args)

        # Extract values
        story = result.story
        print(f"Generated Story: {story}")
        state_changes = result.state_changes

        # Simulate storytelling duration
        await asyncio.sleep(10)

        # Apply state changes with bounds checking
        state.energy = max(state.energy + state_changes['energy'], 0)
        state.happiness = min(state.happiness + state_changes['happiness'], 100)
        state.xp += state_changes['xp']

        # Create memory content
        memory_content = {
            'story': story,
            'state_changes': state_changes,
            'state_snapshot': {
                'energy': state.energy,
                'happiness': state.happiness,
                'xp': state.xp
            }
        }

        # Store memory
        await memory.store_memory(
            content=json.dumps(memory_content, indent=2),
            activity='storytelling',
            source='activity'
        )

        return story

    except Exception as e:
        error_message = f"Error during Pippin's storytelling: {str(e)}"
        print(error_message)
        return "Pippin got a bit wobbly and had to cut his storytelling short today."
