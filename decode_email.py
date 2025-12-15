"""이메일 디코딩 스크립트"""
import base64
import sys
import os

# UTF-8 인코딩 설정
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 제목 디코딩
subject_b64 = '7YWM7Iqk7Yq4IOydtOuplOydvA=='
subject = base64.b64decode(subject_b64).decode('utf-8')

# 본문 디코딩
body_b64 = '''7JWI64WV7ZWY7IS47JqULAoK7J206rKD7J2AIENyZWF0b3IgQ29udHJvbCBDZW50ZXIg7IqI7Y20
7rSA66as7J6QIOqzhOygleyXkOyEnCDrsJzshqHtlZjripQg7YWM7Iqk7Yq4IOydtOuplOydvOye
heuLiOuLpC4KCuygnOuqqTog7YWM7Iqk7Yq4IOydtOuplOydvArrgrTsmqk6IO2FjOyKpO2KuCDr
grTsmqnsnoXri4jri6QuCgrqsJDsgqztlanri4jri6QuCgotLS0KQ3JlYXRvciBDb250cm9sIENl
bnRlcgpTdXBlciBBZG1pbiBFbWFpbCBTZXJ2aWNlCg=='''

body = base64.b64decode(body_b64).decode('utf-8')

print("=" * 70)
print("📧 수신된 테스트 이메일")
print("=" * 70)
print(f"\n보낸 사람: test@localhost")
print(f"받는 사람: k931103@gmail.com")
print(f"제목: {subject}")
print("\n" + "-" * 70)
print("본문:")
print("-" * 70)
print(body)
print("=" * 70)
