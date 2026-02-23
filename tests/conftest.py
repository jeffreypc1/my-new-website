"""Shared fixtures for all tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_config_dir(tmp_path: Path):
    """Provide a temporary config directory and patch shared modules to use it."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture()
def tmp_data_dir(tmp_path: Path):
    """Provide a temporary data directory for case/draft storage."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture()
def sample_client_record():
    """A sample Salesforce client record for template merging tests."""
    return {
        "Id": "003XXXXXXXXXXXX",
        "Customer_ID__c": "1234",
        "FirstName": "Maria",
        "LastName": "Garcia",
        "Name": "Maria Garcia",
        "A_Number__c": "123-456-789",
        "Birthdate": "1990-05-15",
        "Gender__c": "Female",
        "Country__c": "Guatemala",
        "Email": "maria@example.com",
        "MobilePhone": "555-0100",
        "Phone": "555-0101",
        "MailingStreet": "123 Main St",
        "MailingCity": "Los Angeles",
        "MailingState": "CA",
        "MailingPostalCode": "90001",
        "Immigration_Status__c": "Pending",
        "Immigration_Court__c": "Los Angeles",
        "Best_Language__c": "Spanish",
        "Marital_status__c": "Married",
        "CaseNumber__c": "A-12345",
    }
