FUNCTION discover\_and\_invoke(service\_name):



&#x20;   # 1. Resolve through the validating resolver

&#x20;   answer = query\_SVCB(service\_name + ".lab.test", resolver = 127.0.0.1:5301, dnssec\_ok = true)

&#x20;       ON resolver answered SERVFAIL      -> RETURN BOGUS

&#x20;       ON resolver unreachable or timeout -> RETURN UNAVAILABLE

&#x20;       ON name does not exist / no record -> RETURN MALFORMED



&#x20;   # 2. Accept only DNSSEC-validated data

&#x20;   IF answer.AD flag is not set -> RETURN INSECURE



&#x20;   # 3. Check the record is usable

&#x20;   port, host, expected\_digest = parse(answer.first\_SVCB\_record)

&#x20;   IF port missing or out of range, or digest missing or not 64 hex chars

&#x20;       -> RETURN MALFORMED



&#x20;   # 4. Verify the descriptor before trusting or calling the service

&#x20;   descriptor = HTTP\_GET(host, port, "/.well-known/descriptor.json")

&#x20;       ON unreachable or non-200 -> RETURN UNAVAILABLE

&#x20;   IF SHA256(descriptor.raw\_bytes) != expected\_digest

&#x20;       -> RETURN DIGEST\_MISMATCH



&#x20;   # 5. Authenticated call: the service decides access, not DNS

&#x20;   response = HTTP\_GET(host, port, "/probe", header = "Authorization: Bearer " + token)

&#x20;       ON unreachable             -> RETURN UNAVAILABLE

&#x20;       ON status 401 or 403       -> RETURN UNAUTHORISED

&#x20;       ON any other non-200       -> RETURN UNAVAILABLE



&#x20;   RETURN VALID, response.body

