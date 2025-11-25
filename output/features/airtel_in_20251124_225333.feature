# Auto-generated BDD test scenarios
# URL: https://www.airtel.in/
# Generated: 2025-11-24 22:53:33

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.airtel.in" to "Pay Bill" page

    Given the user is on the "https://www.airtel.in/" page
    When the user hovers over the navigation menu "Airtel BlackPay BillView Plans"
    And clicks the link "Pay Bill" from the dropdown
    Then the page URL should change to "https://www.airtel.in/recharge-and-billpay/airtel-black/?icid=header&utm_source=navigation_bar"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.airtel.in" to "View Account" page

    Given the user is on the "https://www.airtel.in/" page
    When the user hovers over the navigation menu "BankView AccountGet New AccountAdd MoneyKnow More"
    And clicks the link "View Account" from the dropdown
    Then the page URL should change to "https://www.airtel.in/bank/login?utm_source=Internal&utm_medium=Header&utm_campaign=Airtel&icid=header"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.airtel.in" to "Login" page

    Given the user is on the "https://www.airtel.in/" page
    When the user hovers over the navigation menu "Account"
    And clicks the link "Login" from the dropdown
    Then the page URL should change to "https://www.airtel.in/s/selfcare?normalLogin"
