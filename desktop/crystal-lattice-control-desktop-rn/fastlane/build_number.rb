# frozen_string_literal: true

module CrystalLatticeMacBuildNumber
  module_function

  def resolve(env:)
    value = first_present(
      env["MACOS_BUILD_NUMBER"],
      env["GITHUB_RUN_NUMBER"],
      "1",
    )

    unless value.match?(/\A[1-9]\d*\z/)
      raise ArgumentError, "macOS build number must be a positive integer"
    end

    value
  end

  def first_present(*values)
    values.find { |value| value && !value.strip.empty? }
  end
end