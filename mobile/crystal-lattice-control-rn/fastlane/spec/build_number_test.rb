# frozen_string_literal: true

require "minitest/autorun"
require_relative "../build_number"

class BuildNumberTest < Minitest::Test
  def test_explicit_number_wins_without_querying_testflight
    queried = false
    result = CrystalLatticeBuildNumber.resolve(
      env: { "IOS_BUILD_NUMBER" => "42", "GITHUB_RUN_NUMBER" => "7" },
      latest_build_number: lambda {
        queried = true
        41
      },
    )

    assert_equal "42", result
    refute queried
  end

  def test_github_number_is_used_when_higher_than_next_testflight_number
    result = CrystalLatticeBuildNumber.resolve(
      env: { "GITHUB_RUN_NUMBER" => "25" },
      latest_build_number: -> { 10 },
    )

    assert_equal "25", result
  end

  def test_next_testflight_number_avoids_a_low_github_counter_collision
    result = CrystalLatticeBuildNumber.resolve(
      env: { "GITHUB_RUN_NUMBER" => "3" },
      latest_build_number: -> { 12 },
    )

    assert_equal "13", result
  end

  def test_next_testflight_number_is_used_without_overrides
    result = CrystalLatticeBuildNumber.resolve(
      env: {},
      latest_build_number: -> { 8 },
    )

    assert_equal "9", result
  end

  def test_invalid_explicit_number_is_rejected
    error = assert_raises(ArgumentError) do
      CrystalLatticeBuildNumber.resolve(
        env: { "IOS_BUILD_NUMBER" => "build-4" },
        latest_build_number: -> { 3 },
      )
    end

    assert_equal "IOS_BUILD_NUMBER must be a positive integer", error.message
  end
end