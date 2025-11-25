# Auto-generated BDD test scenarios
# URL: https://www.apple.com/in/
# Generated: 2025-11-24 22:45:50

Feature: Validate hover interaction on Store

  Scenario: Verify hover behavior on "Store" a

    Given the user is on "https://www.apple.com/in/" page
    When the user hovers over the "Store" a
    Then additional navigation content should become visible

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "In" to "Store" page

    Given the user is on the "https://www.apple.com/in/" page
    When the user hovers over the navigation menu "Mac"
    And clicks the link "Store" from the dropdown
    Then the page URL should change to "https://www.apple.com/in/shop/goto/store"
