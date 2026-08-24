// swift-tools-version: 6.0

import PackageDescription

let package = Package(
  name: "apple-reminders-native",
  platforms: [.macOS(.v14)],
  products: [
    .library(name: "AppleRemindersNativeCore", targets: ["AppleRemindersNativeCore"]),
    .executable(name: "apple-reminders-native", targets: ["apple-reminders-native"]),
  ],
  targets: [
    .target(
      name: "AppleRemindersNativeCore",
      dependencies: []
    ),
    .executableTarget(
      name: "apple-reminders-native",
      dependencies: ["AppleRemindersNativeCore"],
      exclude: ["Resources/Info.plist"],
      linkerSettings: [
        .linkedFramework("CoreLocation"),
        .linkedFramework("EventKit"),
        .unsafeFlags([
          "-Xlinker", "-sectcreate",
          "-Xlinker", "__TEXT",
          "-Xlinker", "__info_plist",
          "-Xlinker", "Sources/apple-reminders-native/Resources/Info.plist",
        ]),
      ]
    ),
    .testTarget(
      name: "AppleRemindersNativeCoreTests",
      dependencies: ["AppleRemindersNativeCore"]
    ),
  ],
  swiftLanguageModes: [.v6]
)
