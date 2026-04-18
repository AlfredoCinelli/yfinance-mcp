BASE_URL ?=
CLIENT_ID ?=
CLIENT_SECRET ?=

.PHONY: get-token
get-token:
	@bash get_token.sh "$(BASE_URL)" "$(CLIENT_ID)" "$(CLIENT_SECRET)"
