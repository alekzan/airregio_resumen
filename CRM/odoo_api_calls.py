import xmlrpc.client

url_demo = "https://autoflujo.odoo.com"
db_demo = "autoflujo"
username_demo = "alejandro_capellan@hotmail.com"
password_demo = "Nadamass1!Odoo1!"


# Create new lead. Returns lead_id


def create_lead(
    lead_name,
    phone_number_id,
    url=url_demo,
    db=db_demo,
    username=username_demo,
    password=password_demo,
):
    # Common endpoint
    common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("Authentication failed")
        return None

    # Object endpoint
    models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))

    # Minimal data for creating a lead
    lead_id = models.execute_kw(
        db,
        uid,
        password,
        "crm.lead",
        "create",
        [
            {
                "name": lead_name,
                "phone": phone_number_id,  # Optional: Add a specific customer ID if needed
                # 'user_id': 1,     # Optional: Assign a salesperson
            }
        ],
    )

    print("Lead created with ID:", lead_id)
    return lead_id


# Example data:
# url = 'https://autoflujo.odoo.com'
# db = 'autoflujo'
# username = 'alejandro_capellan@hotmail.com'
# password = 'Nadamass1!Odoo1!'
# lead_name = 'New Business Opportunity' <<<<----------------

# CALL
# create_lead(url, db, username, password, lead_name)


# Update lead data from lead id. Returns bool depending if success or not.


def update_lead(
    lead_id,
    url=url_demo,
    db=db_demo,
    username=username_demo,
    password=password_demo,
    name=None,
    contact_name=None,
    email_from=None,
    partner_name=None,
    phone=None,
    description=None,
    priority=None,
    tag_ids=None,
    street=None,
    stage_id=None,  # Add stage_id parameter
):
    # Common endpoint
    common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("Authentication failed")
        return False

    # Object endpoint
    models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))

    # Prepare the values dictionary for fields to be updated
    values = {}
    if name is not None:
        values["name"] = name
    if contact_name is not None:
        values["contact_name"] = contact_name
    if email_from is not None:
        values["email_from"] = email_from
    if partner_name is not None:
        values["partner_name"] = partner_name
    if phone is not None:
        values["phone"] = phone
    if description is not None:
        values["description"] = description
    if priority is not None:
        values["priority"] = priority
    if tag_ids is not None:
        values["tag_ids"] = [(6, 0, tag_ids)]  # Update tags with a list of tag IDs
    if street is not None:
        values["street"] = street
    if stage_id is not None:
        values["stage_id"] = stage_id  # Update stage

    # Update the lead
    result = models.execute_kw(
        db, uid, password, "crm.lead", "write", [[lead_id], values]
    )

    if result:
        print("Lead updated successfully.")
    else:
        print("Failed to update the lead.")
    return result


# Example usage:
# lead_id = 15  # The ID of the lead you want to update
#
# update_lead(
#    url,
#    db,
#    username,
#    password,
#    lead_id,
#    name="Updated Opportunity",
#    contact_name="New Contact Name",
#    email_from="new.email@example.com",
#    partner_name="Updated Company Name",
#    phone="+52 9999 9999",
#    description="Updated lead description",
#    priority="2",  # Priority can be "0" (Low), "1" (Normal), "2" (High), etc.
#    tag_ids=[1, 2],  # Replace with actual tag IDs from your database
#    street="123 New Street",
# )


# Create new lead. Returns lead_id
def create_lead_full_data(
    lead_name,
    phone_number_id,
    url=url_demo,
    db=db_demo,
    username=username_demo,
    password=password_demo,
    contact_name=None,
    email_from=None,
    partner_name=None,
    description=None,
    priority=None,
    tag_ids=None,
    street=None,
    stage_id=None,
):
    # Common endpoint
    common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("Authentication failed")
        return None

    # Object endpoint
    models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))

    # Prepare the values dictionary for fields to be created
    values = {"name": lead_name, "phone": phone_number_id}
    if contact_name is not None:
        values["contact_name"] = contact_name
    if email_from is not None:
        values["email_from"] = email_from
    if partner_name is not None:
        values["partner_name"] = partner_name
    if description is not None:
        values["description"] = description
    if priority is not None:
        values["priority"] = priority
    if tag_ids is not None:
        values["tag_ids"] = [(6, 0, tag_ids)]  # Add tags with a list of tag IDs
    if street is not None:
        values["street"] = street
    if stage_id is not None:
        values["stage_id"] = stage_id  # Set stage

    # Create the lead
    lead_id = models.execute_kw(db, uid, password, "crm.lead", "create", [values])

    print("Lead created with ID:", lead_id)
    return lead_id
