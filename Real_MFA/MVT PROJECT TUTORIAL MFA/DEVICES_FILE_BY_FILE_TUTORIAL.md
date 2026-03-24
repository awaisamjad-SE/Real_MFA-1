# Devices App - File by File Tutorial

## 1) What this app does
Devices app tracks where account is accessed from and whether device is trusted.

## 2) models.py
Typical entities:
- Device
- Session
- TrustedDevice (optional)

Device fields:
- user
- fingerprint_hash
- device_name/device_type
- browser/os
- ip/location
- is_verified/is_trusted
- trust_expires_at

Session fields:
- user
- token/session id reference
- device fingerprint
- ip/user agent
- last_activity
- is_active

## 3) views.py
Core pages/actions:
- list devices
- trust or untrust device
- revoke a single session
- revoke all sessions except current

## 4) urls.py
Suggested:
- devices/
- devices/trust/<uuid>/
- devices/revoke/<uuid>/
- sessions/revoke-all/

## 5) utils.py
Helpers:
- parse user agent
- build normalized fingerprint
- compute simple risk score

## 6) signals.py
Safe events:
- new device created -> enqueue notification
- device verified/trusted -> audit log

Do not let signal failure break login transaction.

## 7) templates/devices/
- list.html
- detail.html
- confirm_revoke.html

## 8) security notes
- never auto-trust unknown device
- trust should expire
- allow user revoke from UI
- log location/IP changes

## 9) mini exercise
1. create device model and migration
2. on successful OTP create/update device
3. build trusted devices page
4. implement revoke button and test
