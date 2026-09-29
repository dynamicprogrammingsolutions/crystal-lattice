# frozen_string_literal: true

require "minitest/autorun"
require_relative "../build_number"

class CrystalLatticeMacBuildNumberTest < Minitest::Test
  def test_explicit_build_number_wins
    value = CrystalLatticeMacBuildNumber.resolve(
      env: {
        "MACOS_BUILD_NUMBER" => "42",
        "GITHUB_RUN_NUMBER" => "99",
      },
    )

    assert_equal "42", value
  end

  def test_github_run_number_is_used_in_ci
    value = CrystalLatticeMacBuildNumber.resolve(
      env: { "GITHUB_RUN_NUMBER" => "123" },
    )

    assert_equal "123", value
  end

  def test_local_default_is_one
    assert_equal "1", CrystalLatticeMacBuildNumber.resolve(env: {})
  end

  def test_blank_values_are_ignored
    value = CrystalLatticeMacBuildNumber.resolve(
      env: {
        "MACOS_BUILD_NUMBER" => " ",
        "GITHUB_RUN_NUMBER" => "7",
      },
    )

    assert_equal "7", value
  end

  def test_non_numeric_value_is_rejected
    error = assert_raises(ArgumentError) do
      CrystalLatticeMacBuildNumber.resolve(
        env: { "MACOS_BUILD_NUMBER" => "release-1" },
      )
    end

    assert_match(/positive integer/, error.message)
  end

  def test_zero_is_rejected
    assert_raises(ArgumentError) do
      CrystalLatticeMacBuildNumber.resolve(
        env: { "MACOS_BUILD_NUMBER" => "0" },
      )
    end
  end
end