from typing import Dict
from sqlalchemy.orm import Session
from models.activities import Activity, create_activity, update_activity, delete_activity, force_delete_activity, get_single_activity_by_id, get_activities_by_user, get_activities
from models.bank_accounts import Bank_Account, create_bank_account, update_bank_account, delete_bank_account, force_delete_bank_account, get_single_bank_account_by_id, get_just_single_bank_account_by_id, get_bank_accounts_by_user, set_default_bank_account, get_bank_accounts
from models.categories import Category, create_category, update_category, delete_category, force_delete_category, get_single_category_by_id, get_categories_by_industry_id, get_categories
from models.countries import Country, create_country, update_country, delete_country, force_delete_country, get_single_country_by_id, get_country_by_code, get_countries
from models.countries_currencies import Country_Currency, create_country_currency, update_country_currency, delete_country_currency, force_delete_country_currency, get_single_country_currency_by_id, get_country_currencies, check_country_currency_exists
from models.currencies import Currency, create_currency, update_currency, delete_currency, force_delete_currency, get_single_currency_by_id, get_currency_by_code, get_currencies
from models.general_settings import General_Setting, create_general_setting, update_general_setting, delete_general_setting, get_single_setting_by_id, get_setting_by_name, get_setting_value, get_general_settings
from models.industries import Industry, create_industry, update_industry, delete_industry, force_delete_industry, get_single_industry_by_id, get_single_industry_by_name, get_industries
from models.invites import Invite, create_invite, update_invite, delete_invite, force_delete_invite, get_single_invite_by_id, get_just_single_invite_by_id, get_invites, get_invite_by_email_and_project
from models.invoices import Invoice, create_invoice, update_invoice, delete_invoice, force_delete_invoice, get_single_invoice_by_id, get_invoice_by_reference, get_invoices
from models.milestones import Milestone, create_milestone, update_milestone, delete_milestone, force_delete_milestone, get_single_milestone_by_id, get_project_milestones, get_milestones
from models.password_resets import Password_Reset, create_password_reset, update_password_reset, delete_password_reset, force_delete_password_reset, get_single_password_reset_by_id, get_password_reset_by_token, get_password_resets
from models.profiles import Profile, create_profile, update_profile, update_profile_by_user_id, delete_profile, force_delete_profile, get_single_profile_by_id, get_single_profile_by_user_id, get_profiles
from models.projects import Project, create_project, update_project, delete_project, force_delete_project, get_single_project_by_id, get_just_single_project_by_id, get_projects
from models.roles import Role, create_role, update_role, delete_role, force_delete_role, get_single_role_by_id, get_just_single_role_by_id, get_roles_by_project, get_roles, get_project_ids_from_roles_using_role_ids
from models.roles_users import Role_User, create_role_user, update_role_user, delete_role_user, force_delete_role_user, get_single_role_user_by_id, get_roles_users, get_role_ids_from_roles_users_by_user_id, check_user_has_role
from models.staffs import Staff, create_staff, update_staff, delete_staff, force_delete_staff, get_single_staff_by_id, get_staff_by_user_id, get_staffs
from models.testimonies import Testimony, create_testimony, update_testimony, delete_testimony, force_delete_testimony, get_single_testimony_by_id, get_approved_testimonies, get_testimonies
from models.tokens import Token, create_token, update_token, update_token_by_user_id, update_token_by_user_id_and_token_type, update_token_email, delete_token, force_delete_token, get_single_token_by_id, get_tokens, get_tokens_by_user_id, get_latest_user_token, get_latest_user_token_by_type, get_latest_user_token_by_type_and_status, get_latest_user_token_by_email_and_status, verify_active_token
from models.transactions import Transaction, create_transaction, update_transaction, delete_transaction, force_delete_transaction, get_single_transaction_by_id, get_transaction_by_reference, get_user_transaction_history, get_transactions
from models.users import User, create_user, update_user, delete_user, force_delete_user, get_single_user_by_id, get_just_single_user_by_id, get_single_user_by_email, get_single_user_by_username, get_single_user_by_phone_number, get_users
from models.wallets import Wallet, create_wallet, update_wallet, delete_wallet, force_delete_wallet, get_single_wallet_by_id, get_wallet_by_user_id, get_wallet_by_account_number, get_wallet_by_project_id, get_wallets
import string
import random
from database.db import get_laravel_datetime



def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def create_user_with_relevant_rows(db: Session, username: str=None, phone_number: str=None, email: str = None, password: str = None, country_id: int = None, currency_id: int = None, first_name: str = None, last_name: str = None, is_staff: int = 0):
    user_type = 1
    if is_staff == 1:
        user_type = 2
    user = create_user(db=db, email=email, username=username, phone_number=phone_number, password=password, user_type=user_type, status=1)
    if is_staff == 0:
        create_profile(db=db, user_id=user.id, country_id=country_id, first_name=first_name, last_name=last_name)
        create_wallet(db=db, currency_id=currency_id, user_id=user.id)
    else:
        create_staff(db=db, user_id=user.id, first_name=first_name, last_name=last_name)
    return user

def registration_unique_field_check(db: Session, email: str=None, username: str=None, phone_number: str=None):
    username_check = get_single_user_by_username(db=db, username=username)
    if username_check is not None:
        return {
            'status': False,
            'message': 'Username already exist'
        }
    phone_number_check = get_single_user_by_phone_number(db=db, phone_number=phone_number)
    if phone_number_check is not None:
        return {
            'status': False,
            'message': 'Phone number already exist'
        }
    email_check = get_single_user_by_email(db=db, email=email)
    if email_check is not None:
        return {
            'status': False,
            'message': 'Email already exist'
        }
    else:
        return {
            'status': True,
            'message': 'Validation successful'
        }
