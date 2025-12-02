# Auto-generated BDD test scenarios
# URL: https://newpage.io/
# Generated: 2025-11-24 22:44:33

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "newpage.io" to "Data & AI" page

    Given the user is on the "https://newpage.io/" page
    When the user hovers over the navigation menu "Services"
    And clicks the link "Data & AI" from the dropdown
    Then the page URL should change to "https://newpage.io/artificial-intelligence-and-data/"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "newpage.io" to "Blogs" page

    Given the user is on the "https://newpage.io/" page
    When the user hovers over the navigation menu "Insights"
    And clicks the link "Blogs" from the dropdown
    Then the page URL should change to "https://newpage.io/blog/"
