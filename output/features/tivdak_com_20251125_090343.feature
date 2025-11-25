# Auto-generated BDD test scenarios
# URL: https://www.tivdak.com/patient-stories/
# Generated: 2025-11-25 09:03:43

Feature: Validate Cookie Disclaimer functionality

  Scenario: Verify popup appearance after page load

    Given the user is on "https://www.tivdak.com/patient-stories/" page
    When the page loads
    Then a "Cookie Disclaimer" modal dialog should appear
    When the user clicks the "Manage Cookies" button
    Then the URL should not change
    When the user clicks the "Reject All Cookies" button
    Then the URL should not change


Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "Patient Stories" to "Tivdak and You" page

    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "About Tivdak"
    And clicks the link "Tivdak and You" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/about-tivdak/"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "Patient Stories" to "Overall Survival" page

    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "Results"
    And clicks the link "Overall Survival" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/study-results/"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "Patient Stories" to "Downloads" page

    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "Support"
    And clicks the link "Downloads" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/resources-and-support/"
