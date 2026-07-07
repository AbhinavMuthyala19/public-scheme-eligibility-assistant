from agents.profile_agent import ProfileAgent


agent = ProfileAgent()

result = agent.run(
    """
    I am a 22 year old unemployed woman from Himachal Pradesh.
    I belong to the SC category.
    I want to start a dairy business.
    """
)

print(result)
print()
print("Profile:")
print(result.profile)
print()
print("Missing Fields:", result.missing_fields)
print("Is Complete:", result.is_complete)