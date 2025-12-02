# Auto-generated BDD test scenarios
# URL: https://www.srmist.edu.in/
# Generated: 2025-11-25 12:44:07

Feature: Validate page load popup functionality

  Scenario: Verify modal dialog after page load

    Given the user is on "https://www.srmist.edu.in/" page
    When the page loads
    Then a modal dialog should appear with title ""
    If the modal dialog has buttons, then the available buttons are "[available buttons]"
    If the modal dialog has buttons and changes URL, then the URL does not change

Feature: Validate Open toolbar
					
						Accessibility Tools interaction

  Scenario: Verify behavior when clicking "Open toolbar
					
						Accessibility Tools" button

    Given the user is on "https://www.srmist.edu.in/" page
    When the user clicks the "Open toolbar Accessibility Tools" button
    Then a dropdown menu or overlay should appear
    And the user can close the dialog

Feature: Validate Increase TextIncrease Text functionality

  Scenario: Verify popup modal after clicking Increase TextIncrease Text

    Given the user is on "https://www.srmist.edu.in/" page
    When the user clicks the "Increase TextIncrease Text" button
    Then a modal dialog should appear with title ""
    And no buttons are detected
    Then the URL should not change

Feature: Validate Decrease Text functionality

  Scenario: Verify popup appearance after clicking Decrease Text

    Given the user is on "https://www.srmist.edu.in/" page
    When the user clicks the "Decrease Text" button
    Then a modal dialog should appear with title ""
    [Test 'OK' and 'Cancel' buttons if present, otherwise test only one button]


Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.srmist.edu.in" to "Engineering & Technology" page

    Given the user is on the "https://www.srmist.edu.in/" page
    When the user hovers over the navigation menu "Academics"
    And clicks the link "Engineering & Technology" from the dropdown
    Then the page URL should change to "https://www.srmist.edu.in/college/college-of-engineering-technology/"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.srmist.edu.in" to "Directorate Of Research" page

    Given the user is on the "https://www.srmist.edu.in/" page
    When the user hovers over the navigation menu "Research"
    And clicks the link "Directorate Of Research" from the dropdown
    Then the page URL should change to "https://www.srmist.edu.in/research/"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.srmist.edu.in" to "Overview" page

    Given the user is on the "https://www.srmist.edu.in/" page
    When the user hovers over the navigation menu "Campus life"
    And clicks the link "Overview" from the dropdown
    Then the page URL should change to "https://www.srmist.edu.in/life-at-srm/"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "www.srmist.edu.in" to "About Us" page

    Given the user is on the "https://www.srmist.edu.in/" page
    When the user hovers over the navigation menu "International"
    And clicks the link "About Us" from the dropdown
    Then the page URL should change to "https://www.srmist.edu.in/ir/"
