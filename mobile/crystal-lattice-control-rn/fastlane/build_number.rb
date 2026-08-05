# frozen_string_literal: true

module CrystalLatticeBuildNumber
  module_function

  def resolve(env:, latest_build_number:)
    explicit = normalized(env["IOS_BUILD_NUMBER"], "IOS_BUILD_NUMBER")
    return explicit if explicit

    next_testflight = normalized(
      Integer(latest_build_number.call) + 1,
      "latest TestFlight build number",
    )
    github = normalized(env["GITHUB_RUN_NUMBER"], "GITHUB_RUN_NUMBER")

    return next_testflight unless github

    [Integer(github), Integer(next_testflight)].max.to_s
  end

  def normalized(value, label)
    return nil if value.nil? || value.to_s.strip.empty?

    number = Integer(value.to_s, 10)
    raise ArgumentError, "#{label} must be a positive integer" unless number.positive?

    number.to_s
  rescue ArgumentError
    raise ArgumentError, "#{label} must be a positive integer"
  end
end