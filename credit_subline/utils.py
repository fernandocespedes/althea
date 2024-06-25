def interest_rate_by_100(interest_rate):
    """
    Use case:


    Calculate the initial interest rate based on the given interest rate.


    This utility function assumes that the provided interest rate needs
    to be multiplied by 100 to convert it into the desired format
    for the initial interest rate.


    Parameters:
    - interest_rate (Decimal): The interest rate from the credit subline.


    Returns:
    - Decimal: The calculated initial interest rate.
    """
    return interest_rate * 100
