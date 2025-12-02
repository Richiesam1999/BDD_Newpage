# Auto-generated BDD test scenarios
# URL: https://www.psgtech.edu/
# Generated: 2025-11-25 11:34:42

Feature: No popup interactions detected

  Scenario: Confirm absence of popups

    Given the user is on "https://www.psgtech.edu/" page
    Then no pop-up dialogs should appear during automatic exploration

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.psgtech.edu" to "Alumni
                                                    Albums" page

    Given the user is on the "https://www.psgtech.edu/" page
    When the user hovers over the navigation menu "Alumni"
    And clicks the link "Alumni Albums" from the dropdown
    Then the page URL should change to "https://laudea.psgtech.ac.in/alumni/"
