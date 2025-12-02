# Auto-generated BDD test scenarios
# URL: https://www.nike.com/in/
# Generated: 2025-11-25 09:09:47

Feature: Validate New & Featured menu functionality

  Scenario: Verify dropdown navigation from New & Featured menu

    Given the user is on "https://www.nike.com/in/" page
    When the user clicks the "New & Featured" button
    Then a dropdown menu should appear with product categories
    When the user clicks the "Continue" option from the menu
    Then the page should navigate to the featured products section


Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "In" to "Order Status" page

    Given the user is on the "https://www.nike.com/in/" page
    When the user hovers over the navigation menu "Help"
    And clicks the link "Order Status" from the dropdown
    Then the page URL should change to "https://www.nike.com/in/orders"
