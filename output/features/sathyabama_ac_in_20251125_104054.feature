# Auto-generated BDD test scenarios
# URL: https://www.sathyabama.ac.in/
# Generated: 2025-11-25 10:40:54

Feature: Validate Campus Life menu functionality

  Scenario: Verify dropdown navigation from Campus Life menu

    Given the user is on "https://www.sathyabama.ac.in/" page
    When the user clicks the "CAMPUS LIFE" button
    Then a dropdown menu should appear with sub-menu items
    When the user selects the "360 View" option from the menu
    Then the page should navigate to the 360 view section

Feature: Validate Campus Life menu functionality

  Scenario: Verify dropdown navigation from Campus Life menu

    Given the user is on "https://www.sathyabama.ac.in/" page
    When the user clicks the "CAMPUS LIFE" button
    Then a dropdown menu should appear with sub-menu options
    When the user clicks the "360 View" option from the menu
    Then the page should navigate to the 360 view section

Feature: Validate Campus Life menu functionality

  Scenario: Verify dropdown navigation from Campus Life menu

    Given the user is on "https://www.sathyabama.ac.in/" page
    When the user clicks the "CAMPUS LIFE" button
    Then a dropdown menu should appear with options
    When the user selects the "360 View" option from the menu
    Then the page should navigate to the 360 view section


Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.sathyabama.ac.in" to "About Us" page

    Given the user is on the "https://www.sathyabama.ac.in/" page
    When the user hovers over the navigation menu "Campus Life"
    And clicks the link "About Us" from the dropdown
    Then the page URL should change to "https://www.sathyabama.ac.in/about-us"
