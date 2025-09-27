import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router'
import {
  VStack,
  Text,
  Container,
  Input,
  Box
} from '@chakra-ui/react'
import { useForm } from 'react-hook-form'
import { useState, useEffect } from 'react'
import { FiCheck, FiLock } from 'react-icons/fi'
import { Button } from '../../components/ui/button'
import { Form } from '../../components/ui/form'
import { useServiceMutation, transformApiError } from '../../client/serviceHooks'
import { tokens } from '../../tokens/getTokens'
import { toaster } from '../../components/ui'

interface ResetPasswordForm {
  newPassword: string
  confirmPassword: string
}

interface ResetPasswordSearch {
  token?: string
}

function ResetPasswordComponent() {
  const navigate = useNavigate()
  const { token } = useSearch({ from: '/_layout/reset-password' }) as ResetPasswordSearch
  const [isSuccess, setIsSuccess] = useState(false)
  const { color: colors, semantic } = tokens

  const fonts = {
    heading: "GeneralSans, sans-serif",
    body: "GeneralSans, sans-serif",
  }

  const resetPasswordMutation = useServiceMutation(
    'auth',
    'resetPasswordPasswordResetPost',
    {
      onSuccess: () => {
        setIsSuccess(true)
      },
      onError: (error) => {
        console.log('Reset Password - Mutation onError callback - Raw error:', error)
        const transformedError = transformApiError(error)

        // Show error toast directly
        toaster.create({
          title: 'Error',
          description: transformedError.message,
          type: 'error',
          duration: 7000,
          meta: {
            closable: true,
          },
        })
      },
    }
  )

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordForm>()

  const password = watch('newPassword')

  useEffect(() => {
    if (!token) {
      // Invalid token, redirect to forgot password
      navigate({ to: '/forgot-password' })
    }
  }, [token, navigate])

  const onSubmit = async (data: ResetPasswordForm) => {
    if (!token) return

    await resetPasswordMutation.mutateAsync({
      requestBody: {
        token,
        new_password: data.newPassword,
      },
    })
  }

  return (
    <Box bg={colors.background.default} minH="100vh">
      <Container maxW="2xl" py={{ base: 12, md: 20 }}>
        <VStack gap={8}>
          {/* Header */}
          <VStack gap={4} textAlign="center">
            <Box
              p={4}
              borderRadius="full"
              bg={colors.background.elevated}
              color={colors.brand.primary}
              border="2px solid"
              borderColor={colors.brand.primary}
            >
              {isSuccess ? <FiCheck size={32} /> : <FiLock size={32} />}
            </Box>

            <Text
              fontSize={{ base: "3xl", md: "4xl" }}
              fontWeight="bold"
              color={colors.foreground.default}
              lineHeight="shorter"
              fontFamily={fonts.heading}
            >
              {isSuccess ? (
                <>
                  Password{" "}
                  <Text as="span" color={colors.brand.primary}>
                    Reset Complete
                  </Text>
                </>
              ) : (
                <>
                  Reset Your{" "}
                  <Text as="span" color={colors.brand.primary}>
                    Password
                  </Text>
                </>
              )}
            </Text>
            <Text
              color={colors.foreground.muted}
              fontFamily={fonts.body}
              fontSize="lg"
              maxW="md"
            >
              {isSuccess
                ? "Your password has been successfully reset. You can now use your new password to access your account."
                : "Enter your new password below. Make sure it's strong and secure."
              }
            </Text>
          </VStack>

          {/* Form */}
          <Form maxW="md" w="full">
            <VStack gap={6}>
              {isSuccess ? (
                <VStack gap={6} textAlign="center" py={8}>
                  <Text
                    fontSize="2xl"
                    fontWeight="semibold"
                    color={colors.brand.primary}
                    fontFamily={fonts.heading}
                  >
                    All Set!
                  </Text>
                  <Text
                    color={colors.foreground.muted}
                    fontFamily={fonts.body}
                    fontSize="lg"
                  >
                    Your password has been successfully updated. You can now sign in with your new password.
                  </Text>
                  <Text
                    color={colors.foreground.muted}
                    fontFamily={fonts.body}
                    fontSize="sm"
                  >
                    Keep your password safe and don't share it with anyone.
                  </Text>
                  <Button
                    onClick={() => navigate({ to: '/' })}
                    size="lg"
                    bg={semantic.button.primary.bg.default}
                    color={semantic.button.primary.fg.default}
                    w="full"
                    fontSize="lg"
                    fontFamily={fonts.body}
                  >
                    Continue to Home
                  </Button>
                </VStack>
              ) : (
                <VStack gap={6} w="full" as="form" onSubmit={handleSubmit(onSubmit)}>
                  <VStack gap={2} w="full">
                    <Text
                      color={colors.foreground.default}
                      fontFamily={fonts.body}
                      fontWeight="medium"
                      alignSelf="flex-start"
                    >
                      New Password *
                    </Text>
                    <Input
                      type="password"
                      {...register('newPassword', {
                        required: 'Password is required',
                        minLength: {
                          value: 8,
                          message: 'Password must be at least 8 characters long',
                        },
                        pattern: {
                          value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                          message: 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character',
                        },
                      })}
                      placeholder="Enter your new password"
                      size="lg"
                      bg={colors.background.elevated}
                      border="2px solid"
                      borderColor={colors.border.default}
                      color={colors.foreground.default}
                      _placeholder={{
                        color: colors.foreground.muted,
                      }}
                      _focus={{
                        borderColor: colors.brand.primary,
                        boxShadow: `0 0 0 1px ${colors.brand.primary}`,
                      }}
                      fontFamily={fonts.body}
                    />
                    {errors.newPassword && (
                      <Text
                        color="red.500"
                        fontSize="sm"
                        alignSelf="flex-start"
                        fontFamily={fonts.body}
                      >
                        {errors.newPassword.message}
                      </Text>
                    )}
                  </VStack>

                  <VStack gap={2} w="full">
                    <Text
                      color={colors.foreground.default}
                      fontFamily={fonts.body}
                      fontWeight="medium"
                      alignSelf="flex-start"
                    >
                      Confirm New Password *
                    </Text>
                    <Input
                      type="password"
                      {...register('confirmPassword', {
                        required: 'Please confirm your password',
                        validate: (value) =>
                          value === password || 'Passwords do not match',
                      })}
                      placeholder="Confirm your new password"
                      size="lg"
                      bg={colors.background.elevated}
                      border="2px solid"
                      borderColor={colors.border.default}
                      color={colors.foreground.default}
                      _placeholder={{
                        color: colors.foreground.muted,
                      }}
                      _focus={{
                        borderColor: colors.brand.primary,
                        boxShadow: `0 0 0 1px ${colors.brand.primary}`,
                      }}
                      fontFamily={fonts.body}
                    />
                    {errors.confirmPassword && (
                      <Text
                        color="red.500"
                        fontSize="sm"
                        alignSelf="flex-start"
                        fontFamily={fonts.body}
                      >
                        {errors.confirmPassword.message}
                      </Text>
                    )}
                  </VStack>

                  <Button
                    type="submit"
                    loading={isSubmitting && !resetPasswordMutation.isError}
                    size="lg"
                    bg={semantic.button.primary.bg.default}
                    color={semantic.button.primary.fg.default}
                    w="full"
                    fontSize="lg"
                    fontFamily={fonts.body}
                  >
                    Reset Password
                  </Button>

                  <Text
                    fontSize="sm"
                    textAlign="center"
                    color={colors.foreground.muted}
                    fontFamily={fonts.body}
                  >
                    Need a new reset link?{' '}
                    <Text
                      as="button"
                      onClick={() => navigate({ to: '/forgot-password' })}
                      color={colors.brand.primary}
                      fontWeight="medium"
                      textDecoration="underline"
                      cursor="pointer"
                    >
                      Click here
                    </Text>
                  </Text>
                </VStack>
              )}
            </VStack>
          </Form>
        </VStack>
      </Container>
    </Box>
  )
}

export const Route = createFileRoute('/_layout/reset-password')({
  component: ResetPasswordComponent,
  validateSearch: (search: Record<string, unknown>) => ({
    token: (search.token as string) || undefined,
  }),
})
